import json
import sys
from pathlib import Path

from data_repository import SQLiteDataRepository
from tools import calculate_elo_ratings


def seed_repository(database_path: Path) -> SQLiteDataRepository:
    repository = SQLiteDataRepository(database_path)
    repository.initialize()
    competition_id = "football-data:competition:2021"
    season_id = "football-data:season:1"
    repository.upsert_many(
        "competition",
        [{"id": competition_id, "code": "PL", "name": "Premier League"}],
    )
    repository.upsert_many(
        "season",
        [
            {
                "id": season_id,
                "competition_id": competition_id,
                "name": "2023/24",
                "start_date": "2023-08-01",
                "end_date": "2024-05-31",
            }
        ],
    )
    repository.upsert_many(
        "match",
        [
            {
                "id": "football-data:match:1",
                "competition_id": competition_id,
                "season_id": season_id,
                "utc_date": "2023-08-12T12:00:00Z",
                "status": "FINISHED",
                "home_team_id": "football-data:team:1",
                "away_team_id": "football-data:team:2",
                "home_score": 2,
                "away_score": 0,
            }
        ],
    )
    return repository


def test_calculates_and_persists_elo_idempotently(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    database_path = tmp_path / "footballvs.db"
    repository = seed_repository(database_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["calculate_elo_ratings", "--database", str(database_path)],
    )

    assert calculate_elo_ratings.main() == 0
    first_output = json.loads(capsys.readouterr().out)
    assert calculate_elo_ratings.main() == 0
    second_output = json.loads(capsys.readouterr().out)

    assert first_output["history_records_processed"] == 2
    assert second_output["history_records_stored_total"] == 2
    assert repository.count("elo_history") == 2
    assert repository.count("elo_rating") == 2


def test_reports_missing_competition(tmp_path: Path, monkeypatch, capsys) -> None:
    database_path = tmp_path / "empty.db"
    monkeypatch.setattr(
        sys,
        "argv",
        ["calculate_elo_ratings", "--database", str(database_path)],
    )

    assert calculate_elo_ratings.main() == 2
    assert "not synchronized" in capsys.readouterr().err
