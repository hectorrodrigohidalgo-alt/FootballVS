from datetime import UTC, datetime

import pytest

from data_normalizer import (
    FootballDataNormalizationError,
    normalize_competition,
    normalize_match,
    normalize_season,
    normalize_team,
)

SYNCED_AT = datetime(2026, 8, 9, 15, 30, tzinfo=UTC)


def test_normalizes_competition_and_current_season_reference() -> None:
    result = normalize_competition(
        {
            "id": 2021,
            "code": "pl",
            "name": "Premier League",
            "area": {"name": "England"},
            "currentSeason": {"id": 2403},
        },
        synced_at=SYNCED_AT,
    )

    assert result == {
        "id": "football-data:competition:2021",
        "provider_id": 2021,
        "code": "PL",
        "name": "Premier League",
        "country": "England",
        "current_season_id": "football-data:season:2403",
        "last_synced_at": "2026-08-09T15:30:00Z",
    }


def test_normalizes_season_with_readable_name() -> None:
    result = normalize_season(
        {"id": 2403, "startDate": "2026-08-15", "endDate": "2027-05-23"},
        competition_id="football-data:competition:2021",
    )

    assert result["id"] == "football-data:season:2403"
    assert result["name"] == "2026/27"
    assert result["competition_id"] == "football-data:competition:2021"


def test_normalizes_team_identity_and_optional_crest() -> None:
    result = normalize_team(
        {
            "id": 57,
            "name": "Arsenal FC",
            "shortName": "Arsenal",
            "tla": "ars",
            "crest": "https://crests.football-data.org/57.png",
            "area": {"name": "England"},
        },
        synced_at=SYNCED_AT,
    )

    assert result["id"] == "football-data:team:57"
    assert result["provider_id"] == 57
    assert result["tla"] == "ARS"
    assert result["country"] == "England"


def test_normalizes_finished_match_and_relations() -> None:
    result = normalize_match(
        {
            "id": 537999,
            "competition": {"id": 2021},
            "season": {"id": 2403},
            "utcDate": "2026-08-15T14:00:00Z",
            "status": "finished",
            "matchday": 1,
            "homeTeam": {"id": 57},
            "awayTeam": {"id": 64},
            "score": {
                "winner": "HOME_TEAM",
                "fullTime": {"home": 2, "away": 1},
            },
            "lastUpdated": "2026-08-15T16:00:00Z",
        }
    )

    assert result["id"] == "football-data:match:537999"
    assert result["competition_id"] == "football-data:competition:2021"
    assert result["season_id"] == "football-data:season:2403"
    assert result["home_team_id"] == "football-data:team:57"
    assert result["away_team_id"] == "football-data:team:64"
    assert result["home_score"] == 2
    assert result["away_score"] == 1
    assert result["winner"] == "HOME_TEAM"


def test_normalizes_scheduled_match_with_null_score() -> None:
    result = normalize_match(
        {
            "id": 538000,
            "competition": {"id": 2021},
            "season": {"id": 2403},
            "utcDate": "2026-08-22T14:00:00Z",
            "status": "SCHEDULED",
            "matchday": None,
            "homeTeam": {"id": 57},
            "awayTeam": {"id": 64},
            "score": {"winner": None, "fullTime": {"home": None, "away": None}},
            "lastUpdated": "2026-08-09T10:00:00Z",
        }
    )

    assert result["matchday"] is None
    assert result["home_score"] is None
    assert result["winner"] is None


@pytest.mark.parametrize(
    ("normalizer", "record", "expected_message"),
    [
        (
            lambda record: normalize_competition(record, synced_at=SYNCED_AT),
            {"id": "2021"},
            "id must be an integer",
        ),
        (
            lambda record: normalize_team(record, synced_at=SYNCED_AT),
            {"id": 57, "area": None},
            "area must be an object",
        ),
        (
            normalize_match,
            {"id": 1, "competition": {}},
            "season must be an object",
        ),
    ],
)
def test_rejects_incomplete_or_invalid_provider_records(
    normalizer, record: dict, expected_message: str
) -> None:
    with pytest.raises(FootballDataNormalizationError, match=expected_message):
        normalizer(record)


def test_rejects_sync_timestamp_without_timezone() -> None:
    with pytest.raises(FootballDataNormalizationError, match="timezone"):
        normalize_team(
            {
                "id": 57,
                "name": "Arsenal FC",
                "shortName": "Arsenal",
                "tla": "ARS",
                "area": {"name": "England"},
            },
            synced_at=datetime(2026, 8, 9),
        )
