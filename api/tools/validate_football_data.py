import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from football_data_client import (
    DEFAULT_BASE_URL,
    FootballDataClient,
    FootballDataConfigurationError,
    FootballDataRequestError,
)

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "local.settings.json"


def load_local_configuration(settings_path: Path) -> tuple[str, str]:
    """Lee la clave local sin imprimirla ni copiarla a otra ubicación."""
    try:
        document = json.loads(settings_path.read_text(encoding="utf-8"))
        values = document["Values"]
        api_key = values["FOOTBALL_DATA_API_KEY"]
        base_url = values.get("FOOTBALL_DATA_BASE_URL", DEFAULT_BASE_URL)
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise FootballDataConfigurationError(
            "A valid api/local.settings.json file is required."
        ) from error

    if not isinstance(api_key, str) or not isinstance(base_url, str):
        raise FootballDataConfigurationError(
            "The provider configuration must contain text values."
        )

    return api_key, base_url


def season_start_year(season: dict[str, Any]) -> int | None:
    """Obtiene el año inicial desde una fecha ISO del proveedor."""
    start_date = season.get("startDate")
    if not isinstance(start_date, str) or len(start_date) < 4:
        return None

    try:
        return int(start_date[:4])
    except ValueError:
        return None


def validate_provider_access(
    client: FootballDataClient,
    *,
    max_season_probes: int,
    delay_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Comprueba PL y su ventana reciente sin superar la cuota gratuita."""
    request_count = 0

    def rate_limited_get(
        path: str, query: dict[str, int] | None = None
    ) -> dict[str, Any]:
        nonlocal request_count
        if request_count > 0 and delay_seconds > 0:
            sleep(delay_seconds)
        request_count += 1
        return client.get_json(path, query)

    competition = rate_limited_get("competitions/PL")
    if competition.get("code") != "PL":
        raise FootballDataRequestError(
            "football-data.org returned an unexpected competition."
        )

    raw_seasons = competition.get("seasons")
    if not isinstance(raw_seasons, list):
        raise FootballDataRequestError(
            "The Premier League response does not contain a seasons list."
        )

    seasons_by_year: dict[int, dict[str, Any]] = {}
    for raw_season in raw_seasons:
        if not isinstance(raw_season, dict):
            continue
        year = season_start_year(raw_season)
        if year is not None:
            seasons_by_year[year] = raw_season

    candidate_years = sorted(seasons_by_year, reverse=True)[:max_season_probes]
    accessible_seasons: list[dict[str, Any]] = []
    first_inaccessible_season: int | None = None

    for year in candidate_years:
        try:
            teams_response = rate_limited_get(
                "competitions/PL/teams", {"season": year}
            )
        except FootballDataRequestError as error:
            if error.status_code in {403, 404}:
                first_inaccessible_season = year
                break
            raise

        teams = teams_response.get("teams")
        if not isinstance(teams, list):
            raise FootballDataRequestError(
                "The teams response has an unexpected shape."
            )

        try:
            matches_response = rate_limited_get(
                "competitions/PL/matches",
                {"season": year, "matchday": 1},
            )
        except FootballDataRequestError as error:
            if error.status_code in {403, 404}:
                first_inaccessible_season = year
                break
            raise

        matches = matches_response.get("matches")
        if not isinstance(matches, list):
            raise FootballDataRequestError(
                "The matches response has an unexpected shape."
            )

        season = seasons_by_year[year]
        accessible_seasons.append(
            {
                "start_year": year,
                "start_date": season.get("startDate"),
                "end_date": season.get("endDate"),
                "team_count": len(teams),
                "matchday_1_match_count": len(matches),
            }
        )

    current_season = competition.get("currentSeason")
    return {
        "authenticated": bool(accessible_seasons),
        "competition": {
            "id": competition.get("id"),
            "code": competition.get("code"),
            "name": competition.get("name"),
        },
        "current_season_start_year": (
            season_start_year(current_season)
            if isinstance(current_season, dict)
            else None
        ),
        "listed_season_count": len(seasons_by_year),
        "probed_season_count": len(accessible_seasons)
        + (1 if first_inaccessible_season is not None else 0),
        "accessible_seasons": accessible_seasons,
        "first_inaccessible_season": first_inaccessible_season,
        "request_count": request_count,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate safe access to Premier League data."
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help="Path to the ignored Azure Functions local settings file.",
    )
    parser.add_argument(
        "--max-season-probes",
        type=int,
        default=6,
        choices=range(1, 9),
        metavar="1-8",
        help="Maximum recent seasons to test while respecting the free quota.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=6.5,
        help="Delay between season requests; keep at least 6.1 for real calls.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    if arguments.delay_seconds < 6.1:
        print("delay-seconds must be at least 6.1 for real calls.", file=sys.stderr)
        return 2

    try:
        api_key, base_url = load_local_configuration(arguments.settings)
        client = FootballDataClient(api_key=api_key, base_url=base_url)
        result = validate_provider_access(
            client,
            max_season_probes=arguments.max_season_probes,
            delay_seconds=arguments.delay_seconds,
        )
    except FootballDataConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    except FootballDataRequestError as error:
        print(f"Provider validation failed: {error}", file=sys.stderr)
        return 3

    # El resumen excluye deliberadamente token, cabeceras y respuestas crudas.
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["authenticated"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
