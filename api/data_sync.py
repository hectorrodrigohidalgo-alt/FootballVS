from datetime import UTC, datetime
from typing import Any, Protocol

from data_normalizer import (
    FootballDataNormalizationError,
    normalize_competition,
    normalize_match,
    normalize_season,
    normalize_team,
)
from data_repository import DataRepository


class FootballDataProvider(Protocol):
    """Parte del cliente externo que necesita el sincronizador."""

    def get_json(
        self, path: str, query: dict[str, str | int] | None = None
    ) -> dict[str, Any]: ...


def _required_list(payload: dict[str, Any], field: str) -> list[dict[str, Any]]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise FootballDataNormalizationError(f"{field} must be a list of objects.")
    return value


def _required_mapping(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise FootballDataNormalizationError(f"{field} must be an object.")
    return value


def synchronize_competition_season(
    provider: FootballDataProvider,
    repository: DataRepository,
    *,
    competition_code: str,
    season_start_year: int,
    synced_at: datetime | None = None,
) -> dict[str, Any]:
    """Descarga, normaliza y persiste una temporada de forma repetible."""
    normalized_code = competition_code.strip().upper()
    if not normalized_code:
        raise ValueError("competition_code cannot be empty.")
    if season_start_year < 1900:
        raise ValueError("season_start_year is invalid.")

    sync_timestamp = synced_at or datetime.now(UTC)

    # Primero se descargan todos los recursos. Así, un error remoto no deja una
    # temporada parcialmente actualizada antes de comenzar la persistencia.
    competition_payload = provider.get_json(f"competitions/{normalized_code}")
    teams_payload = provider.get_json(
        f"competitions/{normalized_code}/teams", {"season": season_start_year}
    )
    matches_payload = provider.get_json(
        f"competitions/{normalized_code}/matches", {"season": season_start_year}
    )

    competition = normalize_competition(
        competition_payload, synced_at=sync_timestamp
    )
    season = normalize_season(
        _required_mapping(teams_payload, "season"),
        competition_id=competition["id"],
    )
    teams = [
        normalize_team(team, synced_at=sync_timestamp)
        for team in _required_list(teams_payload, "teams")
    ]
    matches = [
        normalize_match(match) for match in _required_list(matches_payload, "matches")
    ]

    # Los IDs deterministas y los upserts permiten repetir la ejecución. Un
    # documento existente se reemplaza y nunca se crea una segunda copia.
    persisted = {
        "competitions": repository.upsert_many("competition", [competition]),
        "seasons": repository.upsert_many("season", [season]),
        "teams": repository.upsert_many("team", teams),
        "matches": repository.upsert_many("match", matches),
    }
    return {
        "competition_code": normalized_code,
        "season_start_year": season_start_year,
        "synced_at": sync_timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "persisted": persisted,
    }
