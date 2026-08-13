from math import exp, factorial

import pytest

from dixon_coles import (
    DixonColesError,
    DixonColesObservation,
    apply_dixon_coles,
    dixon_coles_tau,
    estimate_rho,
)


def poisson_probability(goals: int, expected: float) -> float:
    return exp(-expected) * expected**goals / factorial(goals)


def baseline_prediction(
    team_1_expected: float = 1.2, team_2_expected: float = 0.8
) -> dict:
    matrix = [
        {
            "team_1_goals": team_1_goals,
            "team_2_goals": team_2_goals,
            "probability": poisson_probability(team_1_goals, team_1_expected)
            * poisson_probability(team_2_goals, team_2_expected),
        }
        for team_1_goals in range(7)
        for team_2_goals in range(7)
    ]
    team_1_win = sum(
        cell["probability"]
        for cell in matrix
        if cell["team_1_goals"] > cell["team_2_goals"]
    )
    draw = sum(
        cell["probability"]
        for cell in matrix
        if cell["team_1_goals"] == cell["team_2_goals"]
    )
    team_2_win = sum(
        cell["probability"]
        for cell in matrix
        if cell["team_1_goals"] < cell["team_2_goals"]
    )
    outside = 1 - sum(cell["probability"] for cell in matrix)
    # La cola exterior es diminuta; se reparte por resultado para construir un
    # contrato base cuya probabilidad 1X2 sume exactamente uno.
    team_1_win += outside
    both_score = (1 - exp(-team_1_expected)) * (1 - exp(-team_2_expected))
    return {
        "model_version": "poisson-v0.1.0",
        "estimated_team_1_goals": team_1_expected,
        "estimated_team_2_goals": team_2_expected,
        "team_1_win_probability": team_1_win,
        "draw_probability": draw,
        "team_2_win_probability": team_2_win,
        "over_2_5_probability": 0.3233235838,
        "under_2_5_probability": 0.6766764162,
        "both_teams_score_probability": both_score,
        "score_matrix": matrix,
        "top_scorelines": sorted(
            matrix, key=lambda item: item["probability"], reverse=True
        )[:3],
        "probability_outside_matrix": outside,
    }


def matrix_cell(prediction: dict, team_1_goals: int, team_2_goals: int) -> float:
    return next(
        cell["probability"]
        for cell in prediction["score_matrix"]
        if cell["team_1_goals"] == team_1_goals
        and cell["team_2_goals"] == team_2_goals
    )


def test_tau_only_corrects_the_four_low_scorelines() -> None:
    assert dixon_coles_tau(0, 0, 1.2, 0.8, -0.1) == pytest.approx(1.096)
    assert dixon_coles_tau(0, 1, 1.2, 0.8, -0.1) == pytest.approx(0.88)
    assert dixon_coles_tau(1, 0, 1.2, 0.8, -0.1) == pytest.approx(0.92)
    assert dixon_coles_tau(1, 1, 1.2, 0.8, -0.1) == pytest.approx(1.1)
    assert dixon_coles_tau(2, 1, 1.2, 0.8, -0.1) == 1


def test_estimates_rho_by_exact_score_log_loss() -> None:
    goalless = [DixonColesObservation(1, 1, 0, 0) for _ in range(10)]
    away_wins = [DixonColesObservation(1, 1, 0, 1) for _ in range(10)]

    assert estimate_rho(goalless).rho == pytest.approx(-0.2)
    assert estimate_rho(away_wins).rho == pytest.approx(0.2)


def test_estimator_prefers_zero_when_rho_cannot_affect_observations() -> None:
    observations = [DixonColesObservation(1.4, 0.9, 2, 1)]

    estimate = estimate_rho(observations)

    assert estimate.rho == pytest.approx(0)
    assert estimate.low_score_observations == 0
    assert estimate.candidates_evaluated == 41


def test_applies_correction_and_recalculates_derived_probabilities() -> None:
    baseline = baseline_prediction()

    adjusted = apply_dixon_coles(
        baseline,
        rho=-0.1,
        rho_training_matches=380,
        rho_training_cutoff="2026-08-01T00:00:00Z",
    )

    assert adjusted["model_version"] == "dixon-coles-v0.1.0"
    assert adjusted["base_model_version"] == "poisson-v0.1.0"
    assert matrix_cell(adjusted, 0, 0) > matrix_cell(baseline, 0, 0)
    assert matrix_cell(adjusted, 1, 1) > matrix_cell(baseline, 1, 1)
    assert matrix_cell(adjusted, 0, 1) < matrix_cell(baseline, 0, 1)
    assert matrix_cell(adjusted, 1, 0) < matrix_cell(baseline, 1, 0)
    assert matrix_cell(adjusted, 2, 2) == matrix_cell(baseline, 2, 2)
    assert (
        adjusted["team_1_win_probability"]
        + adjusted["draw_probability"]
        + adjusted["team_2_win_probability"]
    ) == pytest.approx(1)
    assert sum(cell["probability"] for cell in adjusted["score_matrix"]) + adjusted[
        "probability_outside_matrix"
    ] == pytest.approx(1)
    assert adjusted["over_2_5_probability"] == baseline["over_2_5_probability"]
    assert adjusted["both_teams_score_probability"] > baseline[
        "both_teams_score_probability"
    ]
    assert adjusted["dixon_coles"]["rho_training_matches"] == 380


def test_rejects_invalid_observations_grid_and_adjustment() -> None:
    with pytest.raises(DixonColesError, match="Observed goals"):
        DixonColesObservation(1, 1, -1, 0)
    with pytest.raises(DixonColesError, match="At least one"):
        estimate_rho([])
    with pytest.raises(DixonColesError, match="minimum"):
        estimate_rho([DixonColesObservation(1, 1, 0, 0)], minimum=1, maximum=0)
    with pytest.raises(DixonColesError, match="positive integer"):
        apply_dixon_coles(
            baseline_prediction(),
            rho=0,
            rho_training_matches=1.5,  # type: ignore[arg-type]
            rho_training_cutoff="2026-08-01T00:00:00Z",
        )
    with pytest.raises(DixonColesError, match="non-positive"):
        apply_dixon_coles(
            baseline_prediction(team_1_expected=10, team_2_expected=1),
            rho=0.2,
            rho_training_matches=10,
            rho_training_cutoff="2026-08-01T00:00:00Z",
        )
