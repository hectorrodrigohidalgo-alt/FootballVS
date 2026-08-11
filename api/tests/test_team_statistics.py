from datetime import UTC, datetime

import pytest

from team_statistics import (
    TeamStatisticsError,
    calculate_team_snapshots,
)

COMPETITION_ID = "football-data:competition:2021"
SEASON_ID = "football-data:season:2403"
ARSENAL_ID = "football-data:team:57"
LIVERPOOL_ID = "football-data:team:64"


def match(
    match_id: int,
    *,
    date: str,
    home_score: int | None,
    away_score: int | None,
    status: str = "FINISHED",
) -> dict:
    return {
        "id": f"football-data:match:{match_id}",
        "competition_id": COMPETITION_ID,
        "season_id": SEASON_ID,
        "utc_date": date,
        "status": status,
        "home_team_id": ARSENAL_ID,
        "away_team_id": LIVERPOOL_ID,
        "home_score": home_score,
        "away_score": away_score,
    }


def snapshots_by_team(matches: list[dict]) -> dict[str, dict]:
    snapshots = calculate_team_snapshots(
        matches,
        competition_id=COMPETITION_ID,
        season_id=SEASON_ID,
        calculated_at=datetime(2026, 8, 10, 12, tzinfo=UTC),
    )
    return {snapshot["team_id"]: snapshot for snapshot in snapshots}


def test_calculates_results_goals_points_and_percentages() -> None:
    snapshots = snapshots_by_team(
        [
            match(1, date="2026-08-01T12:00:00Z", home_score=2, away_score=1),
            match(2, date="2026-08-08T12:00:00Z", home_score=0, away_score=0),
            match(3, date="2026-08-15T12:00:00Z", home_score=1, away_score=3),
        ]
    )

    arsenal = snapshots[ARSENAL_ID]
    assert arsenal["matches"] == 3
    assert arsenal["wins"] == 1
    assert arsenal["draws"] == 1
    assert arsenal["losses"] == 1
    assert arsenal["points"] == 4
    assert arsenal["goals_for"] == 3
    assert arsenal["goals_against"] == 4
    assert arsenal["goal_difference"] == -1
    assert arsenal["win_percentage"] == pytest.approx(33.33)
    assert arsenal["points_per_game"] == pytest.approx(1.3333)
    assert arsenal["clean_sheets"] == 1
    assert arsenal["both_teams_scored"] == 2


def test_separates_home_and_away_statistics() -> None:
    reversed_match = {
        **match(2, date="2026-08-08T12:00:00Z", home_score=0, away_score=2),
        "home_team_id": LIVERPOOL_ID,
        "away_team_id": ARSENAL_ID,
    }
    snapshots = snapshots_by_team(
        [
            match(1, date="2026-08-01T12:00:00Z", home_score=1, away_score=1),
            reversed_match,
        ]
    )

    arsenal = snapshots[ARSENAL_ID]
    assert arsenal["home_stats"]["matches"] == 1
    assert arsenal["home_stats"]["draws"] == 1
    assert arsenal["away_stats"]["matches"] == 1
    assert arsenal["away_stats"]["wins"] == 1


def test_ignores_scheduled_matches_but_keeps_teams_in_snapshot() -> None:
    snapshots = snapshots_by_team(
        [
            match(
                1,
                date="2026-08-01T12:00:00Z",
                home_score=None,
                away_score=None,
                status="SCHEDULED",
            )
        ]
    )

    assert snapshots[ARSENAL_ID]["matches"] == 0
    assert snapshots[ARSENAL_ID]["points_per_game"] == 0.0
    assert snapshots[LIVERPOOL_ID]["recent_form"]["last_5"] == []


def test_recent_form_is_chronological_and_limited() -> None:
    results = [
        match(
            index,
            date=f"2026-08-{index:02d}T12:00:00Z",
            home_score=2 if index % 2 else 0,
            away_score=0 if index % 2 else 1,
        )
        for index in range(1, 13)
    ]

    arsenal = snapshots_by_team(list(reversed(results)))[ARSENAL_ID]

    assert arsenal["recent_form"]["last_5"] == ["L", "W", "L", "W", "L"]
    assert len(arsenal["recent_form"]["last_10"]) == 10


def test_rejects_finished_match_without_integer_score() -> None:
    with pytest.raises(TeamStatisticsError, match="integer full-time scores"):
        snapshots_by_team(
            [
                match(
                    1,
                    date="2026-08-01T12:00:00Z",
                    home_score=None,
                    away_score=None,
                )
            ]
        )
