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
    repository.upsert_many(
        "season",
        [
            {
                "id": "previous-season",
                "competition_id": "competition",
                "name": "2025/26",
                "start_date": "2025-08-01",
                "end_date": "2026-05-31",
            },
            {
                "id": "season",
                "competition_id": "competition",
                "name": "2026/27",
                "start_date": "2026-08-01",
                "end_date": "2027-05-31",
            },
        ],
    )
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
    historical_matches = [
        {
            "id": f"historical-{index}",
            "status": "FINISHED",
            "competition_id": "competition",
            "season_id": "previous-season",
            "utc_date": f"2025-09-{index + 1:02d}T20:00:00Z",
            "home_team_id": "team-1" if index % 2 else "team-2",
            "away_team_id": "team-2" if index % 2 else "team-1",
            "home_score": 2 if index % 2 else 1,
            "away_score": 1,
        }
        for index in range(20)
    ]
    repository.upsert_many(
        "match",
        [
            *historical_matches,
            {
                "id": "match-1",
                "status": "FINISHED",
                "competition_id": "competition",
                "season_id": "previous-season",
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
                "season_id": "season",
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
    assert result["head_to_head"]["matches_played"] == 21
    assert result["head_to_head"]["team_1_wins"] == 11
    assert result["prediction"] is not None
    assert result["team_1"]["statistics"]["elo_rating"] is not None
    assert result["model"]["version"] == "poisson-v0.1.0"
    assert result["model"]["elo_version"] == "elo-v0.1.0"
    assert result["model"]["status"] == "validated"
    assert result["model"]["matches_used"] == 21
    assert "score_matrix" not in result["prediction"]
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
