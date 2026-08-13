from datetime import UTC, datetime, timedelta

import pytest

from poisson_model import (
    InsufficientPoissonDataError,
    PoissonModelError,
    PoissonParameters,
    predict_poisson,
)

COMPETITION_ID = "football-data:competition:2021"
TEAM_A = "football-data:team:1"
TEAM_B = "football-data:team:2"


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
    utc_date: datetime,
    home: str,
    away: str,
    score: tuple[int, int],
    status: str = "FINISHED",
) -> dict:
    return {
        "id": f"football-data:match:{identifier}",
        "competition_id": COMPETITION_ID,
        "season_id": season_id,
        "utc_date": utc_date.isoformat().replace("+00:00", "Z"),
        "status": status,
        "home_team_id": home,
        "away_team_id": away,
        "home_score": score[0],
        "away_score": score[1],
    }


def historical_matches(season_id: str, total: int = 20) -> list[dict]:
    start = datetime(2025, 8, 1, 12, tzinfo=UTC)
    return [
        match(
            index,
            season_id=season_id,
            utc_date=start + timedelta(days=index),
            home=TEAM_A if index % 2 else TEAM_B,
            away=TEAM_B if index % 2 else TEAM_A,
            score=(2, 1) if index % 2 else (1, 1),
        )
        for index in range(1, total + 1)
    ]


def prediction(
    matches: list[dict],
    seasons: list[dict],
    *,
    season_id: str,
    venue: str = "team1",
    cutoff: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    parameters: PoissonParameters | None = None,
) -> dict:
    return predict_poisson(
        matches,
        seasons,
        competition_id=COMPETITION_ID,
        season_id=season_id,
        team_1_id=TEAM_A,
        team_2_id=TEAM_B,
        venue=venue,  # type: ignore[arg-type]
        input_data_cutoff=cutoff,
        calculated_at=datetime(2026, 8, 13, 12, tzinfo=UTC),
        parameters=parameters,
    )


def test_generates_complete_experimental_prediction() -> None:
    current_season = season(1, 2025)
    result = prediction(
        historical_matches(current_season["id"]),
        [current_season],
        season_id=current_season["id"],
    )

    assert result["model_version"] == "poisson-v0.1.0"
    assert result["status"] == "experimental"
    assert result["estimated_team_1_goals"] > 0
    assert result["estimated_team_2_goals"] > 0
    assert (
        result["team_1_win_probability"]
        + result["draw_probability"]
        + result["team_2_win_probability"]
    ) == pytest.approx(1)
    assert result["over_2_5_probability"] + result["under_2_5_probability"] == (
        pytest.approx(1)
    )
    assert len(result["score_matrix"]) == 49
    assert len(result["top_scorelines"]) == 3
    assert result["features"]["home_team_raw_matches"] == 10
    assert result["features"]["away_team_raw_matches"] == 10
    assert sum(item["probability"] for item in result["score_matrix"]) + result[
        "probability_outside_matrix"
    ] == pytest.approx(1)


def test_team2_venue_uses_team2_as_home_but_preserves_contract_order() -> None:
    current_season = season(1, 2025)
    matches = historical_matches(current_season["id"])
    team1_home = prediction(
        matches, [current_season], season_id=current_season["id"], venue="team1"
    )
    team2_home = prediction(
        matches, [current_season], season_id=current_season["id"], venue="team2"
    )

    assert team1_home["estimated_team_1_goals"] > team1_home["estimated_team_2_goals"]
    assert team2_home["estimated_team_2_goals"] < team2_home["estimated_team_1_goals"]
    assert team2_home["team_1_id"] == TEAM_A
    assert team2_home["team_2_id"] == TEAM_B


def test_neutral_venue_uses_overall_sample() -> None:
    current_season = season(1, 2025)
    result = prediction(
        historical_matches(current_season["id"]),
        [current_season],
        season_id=current_season["id"],
        venue="neutral",
    )

    assert result["venue"] == "neutral"
    assert result["matches_used"] == 20


def test_rejects_samples_below_league_and_venue_minimums() -> None:
    current_season = season(1, 2025)
    with pytest.raises(InsufficientPoissonDataError) as league_error:
        prediction(
            historical_matches(current_season["id"], total=4),
            [current_season],
            season_id=current_season["id"],
        )
    assert league_error.value.details["required_league_matches"] == 20

    venue_parameters = PoissonParameters(minimum_league_matches=5)
    with pytest.raises(InsufficientPoissonDataError) as venue_error:
        prediction(
            historical_matches(current_season["id"], total=8),
            [current_season],
            season_id=current_season["id"],
            parameters=venue_parameters,
        )
    assert venue_error.value.details["required_team_matches"] == 5


def test_excludes_matches_at_or_after_cutoff_and_scheduled_matches() -> None:
    current_season = season(1, 2025)
    matches = historical_matches(current_season["id"])
    cutoff = datetime(2025, 8, 21, 12, tzinfo=UTC)
    matches.extend(
        [
            match(
                30,
                season_id=current_season["id"],
                utc_date=datetime(2025, 8, 10, 13, tzinfo=UTC),
                home=TEAM_A,
                away=TEAM_B,
                score=(9, 0),
                status="SCHEDULED",
            ),
            match(
                31,
                season_id=current_season["id"],
                utc_date=cutoff,
                home=TEAM_A,
                away=TEAM_B,
                score=(9, 0),
            ),
        ]
    )

    result = prediction(
        matches,
        [current_season],
        season_id=current_season["id"],
        cutoff=cutoff,
        parameters=PoissonParameters(minimum_league_matches=19),
    )
    assert result["matches_used"] == 19


def test_previous_season_is_weighted_but_older_season_is_excluded() -> None:
    old_season = season(1, 2023)
    previous_season = season(2, 2024)
    current_season = season(3, 2025)
    matches = [
        *historical_matches(old_season["id"]),
        *[
            {**item, "id": item["id"] + ":previous", "season_id": previous_season["id"]}
            for item in historical_matches(previous_season["id"])
        ],
        *[
            {**item, "id": item["id"] + ":current", "season_id": current_season["id"]}
            for item in historical_matches(current_season["id"])
        ],
    ]

    result = prediction(
        matches,
        [current_season, old_season, previous_season],
        season_id=current_season["id"],
    )
    assert result["matches_used"] == 40
    assert result["parameters"]["previous_season_weight"] == 0.4


def test_validates_parameters_teams_venue_and_timezone() -> None:
    with pytest.raises(PoissonModelError, match="Minimum match counts"):
        PoissonParameters(minimum_venue_matches=0)

    current_season = season(1, 2025)
    matches = historical_matches(current_season["id"])
    with pytest.raises(PoissonModelError, match="different"):
        predict_poisson(
            matches,
            [current_season],
            competition_id=COMPETITION_ID,
            season_id=current_season["id"],
            team_1_id=TEAM_A,
            team_2_id=TEAM_A,
            venue="neutral",
            input_data_cutoff=datetime(2026, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(PoissonModelError, match="timezone"):
        prediction(
            matches,
            [current_season],
            season_id=current_season["id"],
            cutoff=datetime(2026, 1, 1),
        )


def test_handles_a_valid_sample_containing_only_goalless_draws() -> None:
    current_season = season(1, 2025)
    matches = [
        {**item, "home_score": 0, "away_score": 0}
        for item in historical_matches(current_season["id"])
    ]

    result = prediction(
        matches,
        [current_season],
        season_id=current_season["id"],
    )

    assert result["estimated_team_1_goals"] == 0
    assert result["estimated_team_2_goals"] == 0
    assert result["draw_probability"] == pytest.approx(1)
