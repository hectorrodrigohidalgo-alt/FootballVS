from pathlib import Path

from comparison_service import build_repository_comparison
from data_repository import SQLiteDataRepository


def create_repository(tmp_path: Path) -> SQLiteDataRepository:
    repository = SQLiteDataRepository(tmp_path / "footballvs.db")
    repository.initialize()
    repository.upsert_many(
        "competition",
        [
            {
                "id": "competition",
                "code": "PL",
                "name": "Premier League",
                "country": "England",
                "current_season_id": "season",
            }
        ],
    )
    repository.upsert_many("season", [{"id": "season", "name": "2026/27"}])
    repository.upsert_many(
        "team",
        [
            {
                "id": "team-1",
                "name": "Arsenal FC",
                "short_name": "Arsenal",
                "tla": "ARS",
            },
            {
                "id": "team-2",
                "name": "Liverpool FC",
                "short_name": "Liverpool",
                "tla": "LIV",
            },
        ],
    )
    totals = {
        "matches": 2,
        "wins": 1,
        "draws": 1,
        "losses": 0,
        "win_percentage": 50.0,
        "points_per_game": 2.0,
        "goals_for_per_match": 1.5,
        "goals_against_per_match": 0.5,
        "clean_sheets": 1,
        "both_teams_scored": 1,
    }
    repository.upsert_many(
        "team_snapshot",
        [
            {
                "id": "snapshot-1",
                "team_id": "team-1",
                "season_id": "season",
                "calculated_at": "2026-08-12T10:00:00Z",
                **totals,
                "home_stats": {**totals, "wins": 2},
                "away_stats": totals,
                "recent_form": {"last_5": ["W", "D"]},
            },
            {
                "id": "snapshot-2",
                "team_id": "team-2",
                "season_id": "season",
                "calculated_at": "2026-08-12T11:00:00Z",
                **totals,
                "home_stats": totals,
                "away_stats": {**totals, "losses": 2},
                "recent_form": {"last_5": ["D", "L"]},
            },
        ],
    )
    repository.upsert_many(
        "match",
        [
            {
                "id": "match-1",
                "status": "FINISHED",
                "competition_id": "competition",
                "utc_date": "2025-12-01T20:00:00Z",
                "home_team_id": "team-1",
                "away_team_id": "team-2",
                "home_score": 2,
                "away_score": 1,
            },
            {
                "id": "match-2",
                "status": "SCHEDULED",
                "competition_id": "competition",
                "utc_date": "2026-09-01T20:00:00Z",
                "home_team_id": "team-2",
                "away_team_id": "team-1",
                "home_score": None,
                "away_score": None,
            },
        ],
    )
    return repository


def test_builds_real_comparison_with_venue_and_head_to_head(tmp_path: Path) -> None:
    result = build_repository_comparison(
        create_repository(tmp_path),
        competition_code="PL",
        team_1_id="team-1",
        team_2_id="team-2",
        venue="team1",
    )

    assert result["team_1"]["statistics"]["scope"] == "home"
    assert result["team_2"]["statistics"]["scope"] == "away"
    assert result["head_to_head"]["matches_played"] == 1
    assert result["head_to_head"]["team_1_wins"] == 1
    assert result["prediction"] is None
    assert result["team_1"]["statistics"]["elo_rating"] is None
    assert result["model"]["data_updated_at"] == "2026-08-12T11:00:00Z"


def test_neutral_venue_uses_overall_statistics(tmp_path: Path) -> None:
    result = build_repository_comparison(
        create_repository(tmp_path),
        competition_code="PL",
        team_1_id="team-1",
        team_2_id="team-2",
        venue="neutral",
    )

    assert result["team_1"]["statistics"]["scope"] == "overall"
    assert result["team_2"]["statistics"]["scope"] == "overall"
