from datetime import UTC, datetime
from typing import Any


class TeamStatisticsError(ValueError):
    """Indica que un partido finalizado no permite calcular estadísticas."""


def _empty_totals() -> dict[str, int]:
    return {
        "matches": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "points": 0,
        "goals_for": 0,
        "goals_against": 0,
        "clean_sheets": 0,
        "both_teams_scored": 0,
    }


def _record_result(
    totals: dict[str, int], *, goals_for: int, goals_against: int
) -> str:
    """Actualiza un acumulador y devuelve W, D o L para la forma reciente."""
    totals["matches"] += 1
    totals["goals_for"] += goals_for
    totals["goals_against"] += goals_against
    totals["clean_sheets"] += int(goals_against == 0)
    totals["both_teams_scored"] += int(goals_for > 0 and goals_against > 0)

    if goals_for > goals_against:
        totals["wins"] += 1
        totals["points"] += 3
        return "W"
    if goals_for == goals_against:
        totals["draws"] += 1
        totals["points"] += 1
        return "D"
    totals["losses"] += 1
    return "L"


def _finalize_totals(totals: dict[str, int]) -> dict[str, int | float]:
    """Añade razones calculadas evitando divisiones por cero."""
    matches = totals["matches"]
    return {
        **totals,
        "goal_difference": totals["goals_for"] - totals["goals_against"],
        "win_percentage": round(totals["wins"] * 100 / matches, 2)
        if matches
        else 0.0,
        "points_per_game": round(totals["points"] / matches, 4)
        if matches
        else 0.0,
        "goals_for_per_match": round(totals["goals_for"] / matches, 4)
        if matches
        else 0.0,
        "goals_against_per_match": round(totals["goals_against"] / matches, 4)
        if matches
        else 0.0,
    }


def _calculated_at(value: datetime) -> str:
    if value.tzinfo is None:
        raise TeamStatisticsError("calculated_at must include a timezone.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def calculate_team_snapshots(
    matches: list[dict[str, Any]],
    *,
    competition_id: str,
    season_id: str,
    calculated_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Calcula métricas acumuladas para todos los equipos de una temporada."""
    season_matches = [
        match
        for match in matches
        if match.get("competition_id") == competition_id
        and match.get("season_id") == season_id
    ]
    team_ids = sorted(
        {
            team_id
            for match in season_matches
            for team_id in (match.get("home_team_id"), match.get("away_team_id"))
            if isinstance(team_id, str) and team_id
        }
    )
    states = {
        team_id: {
            "overall": _empty_totals(),
            "home": _empty_totals(),
            "away": _empty_totals(),
            "form": [],
        }
        for team_id in team_ids
    }

    # El orden cronológico hace que los últimos elementos representen la forma
    # más reciente, incluso si el proveedor cambia el orden de su respuesta.
    for match in sorted(season_matches, key=lambda item: str(item.get("utc_date", ""))):
        if match.get("status") != "FINISHED":
            continue
        home_team_id = match.get("home_team_id")
        away_team_id = match.get("away_team_id")
        home_score = match.get("home_score")
        away_score = match.get("away_score")
        if (
            home_team_id not in states
            or away_team_id not in states
            or isinstance(home_score, bool)
            or not isinstance(home_score, int)
            or isinstance(away_score, bool)
            or not isinstance(away_score, int)
        ):
            raise TeamStatisticsError(
                "A finished match requires teams and integer full-time scores."
            )

        home_result = _record_result(
            states[home_team_id]["overall"],
            goals_for=home_score,
            goals_against=away_score,
        )
        _record_result(
            states[home_team_id]["home"],
            goals_for=home_score,
            goals_against=away_score,
        )
        away_result = _record_result(
            states[away_team_id]["overall"],
            goals_for=away_score,
            goals_against=home_score,
        )
        _record_result(
            states[away_team_id]["away"],
            goals_for=away_score,
            goals_against=home_score,
        )
        states[home_team_id]["form"].append(home_result)
        states[away_team_id]["form"].append(away_result)

    timestamp = _calculated_at(calculated_at or datetime.now(UTC))
    return [
        {
            "id": f"footballvs:team-snapshot:{team_id}:{season_id}",
            "team_id": team_id,
            "competition_id": competition_id,
            "season_id": season_id,
            "calculated_at": timestamp,
            **_finalize_totals(state["overall"]),
            "home_stats": _finalize_totals(state["home"]),
            "away_stats": _finalize_totals(state["away"]),
            # La lista conserva orden cronológico: el último valor es el más reciente.
            "recent_form": {
                "last_5": state["form"][-5:],
                "last_10": state["form"][-10:],
            },
        }
        for team_id, state in states.items()
    ]
