import argparse
import json
import sys
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://ambitious-island-0894cf010.7.azurestaticapps.net"


class PublicDeploymentError(RuntimeError):
    """Indica que el sitio público no cumple una comprobación esencial."""


def _request_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/json",
            "User-Agent": "FootballVS/1.0",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise PublicDeploymentError(f"Unexpected HTTP {response.status}.")
            return response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as error:
        raise PublicDeploymentError(
            "The public deployment could not be read."
        ) from error


def _request_json(url: str) -> dict[str, Any]:
    try:
        payload = json.loads(_request_text(url))
    except json.JSONDecodeError as error:
        raise PublicDeploymentError("The public API returned invalid JSON.") from error
    if not isinstance(payload, dict):
        raise PublicDeploymentError("The public API returned an unexpected payload.")
    return payload


def verify_public_deployment(
    base_url: str,
    *,
    request_text: Callable[[str], str] = _request_text,
    request_json: Callable[[str], dict[str, Any]] = _request_json,
) -> dict[str, Any]:
    """Recorre el flujo mínimo que debe seguir funcionando tras publicar."""
    normalized_base_url = base_url.rstrip("/")
    if '<div id="root"></div>' not in request_text(normalized_base_url):
        raise PublicDeploymentError("The React application shell was not found.")

    health = request_json(f"{normalized_base_url}/api/v1/health")
    if health.get("status") != "ok":
        raise PublicDeploymentError("The health endpoint is not ready.")

    competitions = request_json(f"{normalized_base_url}/api/v1/competitions")
    competition_items = competitions.get("data")
    if competitions.get("meta", {}).get("source") != "repository":
        raise PublicDeploymentError("The API is not using the real repository.")
    if not isinstance(competition_items, list) or not competition_items:
        raise PublicDeploymentError("No public competition is available.")
    competition_id = competition_items[0].get("id")
    if not isinstance(competition_id, str) or not competition_id:
        raise PublicDeploymentError("The competition identifier is invalid.")

    teams_url = (
        f"{normalized_base_url}/api/v1/competitions/{quote(competition_id)}/teams"
    )
    teams = request_json(teams_url)
    team_items = teams.get("data")
    if not isinstance(team_items, list) or len(team_items) < 2:
        raise PublicDeploymentError("Fewer than two teams are available.")

    team_1_id = team_items[0].get("id")
    team_2_id = team_items[1].get("id")
    if not all(isinstance(value, str) and value for value in (team_1_id, team_2_id)):
        raise PublicDeploymentError("A team identifier is invalid.")
    comparison_query = urlencode(
        {
            "competition": competition_id,
            "team1": team_1_id,
            "team2": team_2_id,
            "venue": "team1",
        }
    )
    comparison = request_json(
        f"{normalized_base_url}/api/v1/comparisons?{comparison_query}"
    )
    comparison_data = comparison.get("data")
    if comparison.get("meta", {}).get("source") != "repository":
        raise PublicDeploymentError("The comparison is not using the repository.")
    if not isinstance(comparison_data, dict):
        raise PublicDeploymentError("The comparison payload is invalid.")
    model = comparison_data.get("model")
    if not isinstance(model, dict) or not model.get("version"):
        raise PublicDeploymentError("The statistical model metadata is missing.")

    return {
        "status": "ok",
        "source": "repository",
        "competition": competition_id,
        "team_count": len(team_items),
        "comparison": [team_1_id, team_2_id],
        "model_version": model["version"],
        "prediction_available": bool(model.get("is_available")),
    }


def verify_eventually(
    base_url: str,
    *,
    attempts: int,
    delay_seconds: float,
    verify: Callable[[str], dict[str, Any]] = verify_public_deployment,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Reintenta el flujo completo mientras Azure propaga el despliegue."""
    last_error: PublicDeploymentError | None = None
    for attempt in range(attempts):
        try:
            return verify(base_url)
        except PublicDeploymentError as error:
            last_error = error
            if attempt < attempts - 1:
                sleep(delay_seconds)
    raise PublicDeploymentError(
        "Public deployment verification failed."
    ) from last_error


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the public FootballVS MVP.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--delay-seconds", type=float, default=10)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    if arguments.attempts < 1 or arguments.delay_seconds < 0:
        print("Smoke test retry settings are invalid.", file=sys.stderr)
        return 2
    try:
        result = verify_eventually(
            arguments.base_url,
            attempts=arguments.attempts,
            delay_seconds=arguments.delay_seconds,
        )
    except PublicDeploymentError as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
