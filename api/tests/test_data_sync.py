from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data_repository import SQLiteDataRepository
from data_sync import synchronize_competition_season


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str | int] | None]] = []

    def get_json(
        self, path: str, query: dict[str, str | int] | None = None
    ) -> dict[str, Any]:
        self.calls.append((path, query))
        if path == "competitions/PL":
            return {
                "id": 2021,
                "code": "PL",
                "name": "Premier League",
                "area": {"name": "England"},
                "currentSeason": {"id": 2403},
            }
        if path.endswith("/teams"):
            return {
                "season": {
                    "id": 2403,
                    "startDate": "2026-08-15",
                    "endDate": "2027-05-23",
                },
                "teams": [
                    {
                        "id": 57,
                        "name": "Arsenal FC",
                        "shortName": "Arsenal",
                        "tla": "ARS",
                        "crest": None,
                        "area": {"name": "England"},
                    },
                    {
                        "id": 64,
                        "name": "Liverpool FC",
                        "shortName": "Liverpool",
                        "tla": "LIV",
                        "crest": None,
                        "area": {"name": "England"},
                    },
                ],
            }
        return {
            "matches": [
                {
                    "id": 537999,
                    "competition": {"id": 2021},
                    "season": {"id": 2403},
                    "utcDate": "2026-08-15T14:00:00Z",
                    "status": "SCHEDULED",
                    "matchday": 1,
                    "homeTeam": {"id": 57},
                    "awayTeam": {"id": 64},
                    "score": {
                        "winner": None,
                        "fullTime": {"home": None, "away": None},
                    },
                    "lastUpdated": "2026-08-09T10:00:00Z",
                }
            ]
        }


def test_sync_is_idempotent_when_executed_twice(tmp_path: Path) -> None:
    repository = SQLiteDataRepository(tmp_path / "footballvs.db")
    repository.initialize()
    provider = FakeProvider()
    synced_at = datetime(2026, 8, 9, 18, tzinfo=UTC)

    first = synchronize_competition_season(
        provider,
        repository,
        competition_code="pl",
        season_start_year=2026,
        synced_at=synced_at,
    )
    second = synchronize_competition_season(
        provider,
        repository,
        competition_code="PL",
        season_start_year=2026,
        synced_at=synced_at,
    )

    assert first == second
    assert repository.count("competition") == 1
    assert repository.count("season") == 1
    assert repository.count("team") == 2
    assert repository.count("match") == 1
    assert len(provider.calls) == 6


def test_sync_updates_existing_match_instead_of_duplicating_it(tmp_path: Path) -> None:
    repository = SQLiteDataRepository(tmp_path / "footballvs.db")
    repository.initialize()
    provider = FakeProvider()

    synchronize_competition_season(
        provider,
        repository,
        competition_code="PL",
        season_start_year=2026,
    )
    repository.upsert_many(
        "match",
        [
            {
                **repository.list_documents("match")[0],
                "status": "FINISHED",
                "home_score": 2,
                "away_score": 1,
            }
        ],
    )

    assert repository.count("match") == 1
    assert repository.list_documents("match")[0]["status"] == "FINISHED"
