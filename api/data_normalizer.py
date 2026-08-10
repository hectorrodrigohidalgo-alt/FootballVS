from datetime import UTC, datetime
from typing import Any


class FootballDataNormalizationError(ValueError):
    """Indica que un registro externo no cumple el contrato interno mínimo."""


def _required_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    value = record.get(field)
    if not isinstance(value, dict):
        raise FootballDataNormalizationError(f"{field} must be an object.")
    return value


def _required_text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FootballDataNormalizationError(f"{field} must be non-empty text.")
    return value.strip()


def _required_int(record: dict[str, Any], field: str) -> int:
    value = record.get(field)
    # bool hereda de int en Python, pero no es un identificador válido.
    if isinstance(value, bool) or not isinstance(value, int):
        raise FootballDataNormalizationError(f"{field} must be an integer.")
    return value


def _optional_text(record: dict[str, Any], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise FootballDataNormalizationError(f"{field} must be text or null.")
    normalized = value.strip()
    return normalized or None


def _optional_int(record: dict[str, Any], field: str) -> int | None:
    value = record.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise FootballDataNormalizationError(f"{field} must be an integer or null.")
    return value


def _timestamp(value: datetime) -> str:
    """Convierte marcas horarias a UTC para comparar y persistir consistentemente."""
    if value.tzinfo is None:
        raise FootballDataNormalizationError(
            "The sync timestamp must include a timezone."
        )
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _entity_id(entity: str, provider_id: int) -> str:
    """Genera una clave estable; repetir una importación produce el mismo ID."""
    return f"football-data:{entity}:{provider_id}"


def normalize_competition(
    record: dict[str, Any], *, synced_at: datetime
) -> dict[str, Any]:
    """Adapta una competición de football-data.org al modelo de FootballVS."""
    provider_id = _required_int(record, "id")
    area = _required_mapping(record, "area")
    current_season = record.get("currentSeason")
    current_season_id = None
    if current_season is not None:
        if not isinstance(current_season, dict):
            raise FootballDataNormalizationError("currentSeason must be an object.")
        season_provider_id = _required_int(current_season, "id")
        current_season_id = _entity_id("season", season_provider_id)

    return {
        "id": _entity_id("competition", provider_id),
        "provider_id": provider_id,
        "code": _required_text(record, "code").upper(),
        "name": _required_text(record, "name"),
        "country": _required_text(area, "name"),
        "current_season_id": current_season_id,
        "last_synced_at": _timestamp(synced_at),
    }


def normalize_season(
    record: dict[str, Any], *, competition_id: str
) -> dict[str, Any]:
    """Normaliza una temporada y conserva su relación con la competición."""
    provider_id = _required_int(record, "id")
    start_date = _required_text(record, "startDate")
    end_date = _required_text(record, "endDate")
    start_year = start_date[:4]
    end_year = end_date[:4]
    if not (start_year.isdigit() and end_year.isdigit()):
        raise FootballDataNormalizationError("Season dates must begin with a year.")

    return {
        "id": _entity_id("season", provider_id),
        "provider_id": provider_id,
        "competition_id": competition_id,
        "name": f"{start_year}/{end_year[-2:]}",
        "start_date": start_date,
        "end_date": end_date,
    }


def normalize_team(record: dict[str, Any], *, synced_at: datetime) -> dict[str, Any]:
    """Reduce un equipo externo a identidad y metadatos útiles para el MVP."""
    provider_id = _required_int(record, "id")
    area = _required_mapping(record, "area")
    return {
        "id": _entity_id("team", provider_id),
        "provider_id": provider_id,
        "name": _required_text(record, "name"),
        "short_name": _required_text(record, "shortName"),
        "tla": _required_text(record, "tla").upper(),
        "crest_url": _optional_text(record, "crest"),
        "country": _required_text(area, "name"),
        "last_synced_at": _timestamp(synced_at),
    }


def normalize_match(record: dict[str, Any]) -> dict[str, Any]:
    """Convierte un partido y sus referencias sin conservar la respuesta cruda."""
    provider_id = _required_int(record, "id")
    competition = _required_mapping(record, "competition")
    season = _required_mapping(record, "season")
    home_team = _required_mapping(record, "homeTeam")
    away_team = _required_mapping(record, "awayTeam")
    score = _required_mapping(record, "score")
    full_time = _required_mapping(score, "fullTime")

    return {
        "id": _entity_id("match", provider_id),
        "provider_id": provider_id,
        "competition_id": _entity_id(
            "competition", _required_int(competition, "id")
        ),
        "season_id": _entity_id("season", _required_int(season, "id")),
        "utc_date": _required_text(record, "utcDate"),
        "status": _required_text(record, "status").upper(),
        "matchday": _optional_int(record, "matchday"),
        "home_team_id": _entity_id("team", _required_int(home_team, "id")),
        "away_team_id": _entity_id("team", _required_int(away_team, "id")),
        "home_score": _optional_int(full_time, "home"),
        "away_score": _optional_int(full_time, "away"),
        "winner": _optional_text(score, "winner"),
        "updated_at": _required_text(record, "lastUpdated"),
    }
