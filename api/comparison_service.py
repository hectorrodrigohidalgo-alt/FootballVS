from datetime import UTC, datetime
from typing import Any

from data_repository import DataRepository
from elo_rating import EloParameters, EloRatingError, calculate_elo_history
from poisson_model import (
    InsufficientPoissonDataError,
    PoissonModelError,
    PoissonParameters,
    predict_poisson,
)


class ComparisonNotFoundError(LookupError):
    """Indica que la competición, temporada o equipos no están disponibles."""


def _find_by_id(documents: list[dict[str, Any]], document_id: str) -> dict[str, Any]:
    document = next((item for item in documents if item.get("id") == document_id), None)
    if document is None:
        raise ComparisonNotFoundError(f"Document {document_id} was not found.")
    return document


def _public_team(
    team: dict[str, Any],
    snapshot: dict[str, Any],
    scope: str,
    elo_rating: float | None,
) -> dict[str, Any]:
    selected = snapshot if scope == "overall" else snapshot[f"{scope}_stats"]
    return {
        "id": team["id"],
        "name": team["name"],
        "short_name": team["short_name"],
        "tla": team["tla"],
        "statistics": {
            "scope": scope,
            "matches_played": selected["matches"],
            "wins": selected["wins"],
            "draws": selected["draws"],
            "losses": selected["losses"],
            "win_percentage": selected["win_percentage"],
            "points_per_game": selected["points_per_game"],
            "goals_for_per_match": selected["goals_for_per_match"],
            "goals_against_per_match": selected["goals_against_per_match"],
            "clean_sheets": selected["clean_sheets"],
            "both_teams_scored": selected["both_teams_scored"],
            "recent_form": snapshot["recent_form"]["last_5"],
            "elo_rating": elo_rating,
        },
    }


def _current_elo_ratings(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    competition_id: str,
) -> dict[str, float]:
    """Calcula Elo desde el historial para que nunca dependa de un cache obsoleto."""
    try:
        _, ratings = calculate_elo_history(
            matches,
            seasons,
            competition_id=competition_id,
            parameters=EloParameters(),
        )
    except EloRatingError:
        return {}
    return {item["team_id"]: item["rating"] for item in ratings}


def _public_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    """Expone resultados útiles sin transportar la matriz interna 7 × 7."""
    fields = (
        "team_1_win_probability",
        "draw_probability",
        "team_2_win_probability",
        "estimated_team_1_goals",
        "estimated_team_2_goals",
        "over_2_5_probability",
        "under_2_5_probability",
        "both_teams_score_probability",
        "top_scorelines",
    )
    return {field: prediction[field] for field in fields}


def _head_to_head(
    matches: list[dict[str, Any]],
    competition_id: str,
    team_1_id: str,
    team_2_id: str,
) -> dict[str, Any]:
    meetings = [
        match
        for match in matches
        if match.get("status") == "FINISHED"
        and match.get("competition_id") == competition_id
        and {match.get("home_team_id"), match.get("away_team_id")}
        == {team_1_id, team_2_id}
    ]
    meetings.sort(key=lambda match: str(match.get("utc_date", "")), reverse=True)
    team_1_wins = 0
    team_2_wins = 0
    draws = 0
    for match in meetings:
        if match["home_score"] == match["away_score"]:
            draws += 1
        elif (
            match["home_score"] > match["away_score"]
            and match["home_team_id"] == team_1_id
        ) or (
            match["away_score"] > match["home_score"]
            and match["away_team_id"] == team_1_id
        ):
            team_1_wins += 1
        else:
            team_2_wins += 1
    return {
        "matches_played": len(meetings),
        "team_1_wins": team_1_wins,
        "draws": draws,
        "team_2_wins": team_2_wins,
        "recent_matches": meetings[:10],
    }


def build_repository_comparison(
    repository: DataRepository,
    *,
    competition_code: str,
    team_1_id: str,
    team_2_id: str,
    venue: str,
) -> dict[str, Any]:
    """Compone una comparación trazable usando sólo documentos persistidos."""
    competition = next(
        (
            item
            for item in repository.list_documents("competition")
            if item.get("code") == competition_code
        ),
        None,
    )
    if competition is None:
        raise ComparisonNotFoundError("The competition was not found.")
    seasons = repository.list_documents("season")
    season = _find_by_id(seasons, competition["current_season_id"])
    teams = repository.list_documents("team")
    team_1 = _find_by_id(teams, team_1_id)
    team_2 = _find_by_id(teams, team_2_id)
    snapshots = repository.list_documents("team_snapshot")

    def snapshot_for(team_id: str) -> dict[str, Any]:
        snapshot = next(
            (
                item
                for item in snapshots
                if item.get("team_id") == team_id
                and item.get("season_id") == season["id"]
            ),
            None,
        )
        if snapshot is None:
            raise ComparisonNotFoundError("Statistics are not available.")
        return snapshot

    snapshot_1 = snapshot_for(team_1_id)
    snapshot_2 = snapshot_for(team_2_id)
    matches = repository.list_documents("match")
    elo_ratings = _current_elo_ratings(matches, seasons, competition["id"])
    team_1_scope = (
        "home" if venue == "team1" else "away" if venue == "team2" else "overall"
    )
    team_2_scope = (
        "away" if venue == "team1" else "home" if venue == "team2" else "overall"
    )
    cutoff = datetime.now(UTC)
    prediction = None
    prediction_message = None
    matches_used = 0
    try:
        full_prediction = predict_poisson(
            matches,
            seasons,
            competition_id=competition["id"],
            season_id=season["id"],
            team_1_id=team_1_id,
            team_2_id=team_2_id,
            venue=venue,  # type: ignore[arg-type]
            input_data_cutoff=cutoff,
            parameters=PoissonParameters(),
        )
        prediction = _public_prediction(full_prediction)
        matches_used = full_prediction["matches_used"]
    except InsufficientPoissonDataError as error:
        prediction_message = str(error)
    except PoissonModelError:
        prediction_message = "The prediction could not be calculated."

    return {
        "competition": {
            "id": competition["code"],
            "name": competition["name"],
            "country": competition["country"],
            "season": season["name"],
        },
        "team_1": _public_team(
            team_1, snapshot_1, team_1_scope, elo_ratings.get(team_1_id)
        ),
        "team_2": _public_team(
            team_2, snapshot_2, team_2_scope, elo_ratings.get(team_2_id)
        ),
        "venue": venue,
        "head_to_head": _head_to_head(
            matches,
            competition["id"],
            team_1_id,
            team_2_id,
        ),
        "prediction": prediction,
        "model": {
            "version": "poisson-v0.1.0",
            "elo_version": "elo-v0.1.0",
            "status": "validated",
            "is_available": prediction is not None,
            "message": prediction_message,
            "input_data_cutoff": cutoff.isoformat().replace("+00:00", "Z"),
            "matches_used": matches_used,
            "data_updated_at": max(
                snapshot_1["calculated_at"], snapshot_2["calculated_at"]
            ),
        },
    }
