from datetime import UTC, datetime

import pytest

from elo_rating import (
    EloParameters,
    EloRatingError,
    calculate_elo_history,
    expected_score,
)

COMPETITION_ID = "football-data:competition:2021"
TEAM_A = "football-data:team:1"
TEAM_B = "football-data:team:2"
TEAM_C = "football-data:team:3"
TEAM_D = "football-data:team:4"
CALCULATED_AT = datetime(2026, 8, 13, 12, tzinfo=UTC)


def season(identifier: int, year: int) -> dict:
    return {
        "id": f"football-data:season:{identifier}",
        "competition_id": COMPETITION_ID,
        "name": f"{year}/{str(year + 1)[-2:]}",
        "start_date": f"{year}-08-01",
        "end_date": f"{year + 1}-05-31",
    }


def match(
    identifier: int,
    *,
    season_id: str,
    utc_date: str,
    home: str = TEAM_A,
    away: str = TEAM_B,
    score: tuple[int, int] = (1, 0),
    status: str = "FINISHED",
) -> dict:
    return {
        "id": f"football-data:match:{identifier}",
        "competition_id": COMPETITION_ID,
        "season_id": season_id,
        "utc_date": utc_date,
        "status": status,
        "home_team_id": home,
        "away_team_id": away,
        "home_score": score[0],
        "away_score": score[1],
    }


def records_by_team(records: list[dict]) -> dict[str, dict]:
    return {record["team_id"]: record for record in records}


def test_expected_score_is_balanced_and_complementary() -> None:
    assert expected_score(1500, 1500) == pytest.approx(0.5)
    assert expected_score(1600, 1400) + expected_score(1400, 1600) == pytest.approx(1)


def test_calculates_zero_sum_changes_and_auditable_records() -> None:
    current_season = season(1, 2023)
    history, ratings = calculate_elo_history(
        [
            match(
                1,
                season_id=current_season["id"],
                utc_date="2023-08-12T12:00:00Z",
            )
        ],
        [current_season],
        competition_id=COMPETITION_ID,
        calculated_at=CALCULATED_AT,
    )
    records = records_by_team(history)
    current = records_by_team(ratings)

    assert len(history) == 2
    assert records[TEAM_A]["rating_before"] == 1500
    assert records[TEAM_A]["venue_adjustment"] == 65
    assert records[TEAM_A]["actual_score"] == 1
    assert records[TEAM_A]["rating_change"] == pytest.approx(
        -records[TEAM_B]["rating_change"]
    )
    assert current[TEAM_A]["rating"] == pytest.approx(records[TEAM_A]["rating_after"])
    assert current[TEAM_B]["rating"] == pytest.approx(records[TEAM_B]["rating_after"])
    assert records[TEAM_A]["model_version"] == "elo-v0.1.0"


def test_ignores_scheduled_matches() -> None:
    current_season = season(1, 2023)
    history, ratings = calculate_elo_history(
        [
            match(
                1,
                season_id=current_season["id"],
                utc_date="2023-08-12T12:00:00Z",
                status="SCHEDULED",
            )
        ],
        [current_season],
        competition_id=COMPETITION_ID,
        calculated_at=CALCULATED_AT,
    )

    assert history == []
    assert {item["rating"] for item in ratings} == {1500}


def test_simultaneous_matches_use_ratings_before_the_block() -> None:
    current_season = season(1, 2023)
    history, _ = calculate_elo_history(
        [
            match(
                1,
                season_id=current_season["id"],
                utc_date="2023-08-12T12:00:00Z",
                home=TEAM_A,
                away=TEAM_B,
            ),
            match(
                2,
                season_id=current_season["id"],
                utc_date="2023-08-12T12:00:00Z",
                home=TEAM_C,
                away=TEAM_D,
                score=(0, 1),
            ),
        ],
        [current_season],
        competition_id=COMPETITION_ID,
        calculated_at=CALCULATED_AT,
    )

    assert {record["rating_before"] for record in history} == {1500}


def test_orders_postponed_match_by_utc_date_not_input_or_matchday() -> None:
    current_season = season(1, 2023)
    later = match(
        1,
        season_id=current_season["id"],
        utc_date="2024-02-01T12:00:00Z",
    )
    later["matchday"] = 3
    earlier = match(
        2,
        season_id=current_season["id"],
        utc_date="2023-09-01T12:00:00Z",
        score=(0, 1),
    )
    earlier["matchday"] = 10

    history, _ = calculate_elo_history(
        [later, earlier],
        [current_season],
        competition_id=COMPETITION_ID,
        calculated_at=CALCULATED_AT,
    )

    team_a_history = [record for record in history if record["team_id"] == TEAM_A]
    assert [record["match_id"] for record in team_a_history] == [
        earlier["id"],
        later["id"],
    ]
    assert team_a_history[1]["rating_before"] == pytest.approx(
        team_a_history[0]["rating_after"]
    )


def test_applies_retention_and_promoted_rating_between_seasons() -> None:
    first_season = season(1, 2023)
    second_season = season(2, 2024)
    history, _ = calculate_elo_history(
        [
            match(
                1,
                season_id=first_season["id"],
                utc_date="2023-08-12T12:00:00Z",
            ),
            match(
                2,
                season_id=second_season["id"],
                utc_date="2024-08-12T12:00:00Z",
                home=TEAM_A,
                away=TEAM_C,
            ),
        ],
        [second_season, first_season],
        competition_id=COMPETITION_ID,
        calculated_at=CALCULATED_AT,
    )
    first_records = records_by_team(history[:2])
    second_records = records_by_team(history[2:])
    expected_retained = 1500 + (first_records[TEAM_A]["rating_after"] - 1500) * 0.75

    assert second_records[TEAM_A]["rating_before"] == pytest.approx(expected_retained)
    assert second_records[TEAM_C]["rating_before"] == 1400


def test_rejects_duplicate_team_inside_simultaneous_block() -> None:
    current_season = season(1, 2023)
    with pytest.raises(EloRatingError, match="twice"):
        calculate_elo_history(
            [
                match(
                    1,
                    season_id=current_season["id"],
                    utc_date="2023-08-12T12:00:00Z",
                    home=TEAM_A,
                    away=TEAM_B,
                ),
                match(
                    2,
                    season_id=current_season["id"],
                    utc_date="2023-08-12T12:00:00Z",
                    home=TEAM_A,
                    away=TEAM_C,
                ),
            ],
            [current_season],
            competition_id=COMPETITION_ID,
            calculated_at=CALCULATED_AT,
        )


def test_validates_parameters_and_finished_scores() -> None:
    with pytest.raises(EloRatingError, match="between zero and one"):
        EloParameters(season_retention=1.1)

    current_season = season(1, 2023)
    invalid_match = match(
        1,
        season_id=current_season["id"],
        utc_date="2023-08-12T12:00:00Z",
    )
    invalid_match["home_score"] = None
    with pytest.raises(EloRatingError, match="integer full-time scores"):
        calculate_elo_history(
            [invalid_match],
            [current_season],
            competition_id=COMPETITION_ID,
            calculated_at=CALCULATED_AT,
        )
