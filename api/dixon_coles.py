from dataclasses import dataclass
from math import exp, factorial, isfinite, log
from typing import Any


class DixonColesError(ValueError):
    """Indica parámetros o predicciones incompatibles con Dixon-Coles."""


@dataclass(frozen=True)
class DixonColesObservation:
    home_expected_goals: float
    away_expected_goals: float
    home_goals: int
    away_goals: int
    match_id: str = ""

    def __post_init__(self) -> None:
        expected_values = (self.home_expected_goals, self.away_expected_goals)
        if any(
            isinstance(value, bool) or not isfinite(value) or value < 0
            for value in expected_values
        ):
            raise DixonColesError("Expected goals must be finite and non-negative.")
        score_values = (self.home_goals, self.away_goals)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in score_values
        ):
            raise DixonColesError("Observed goals must be non-negative integers.")


@dataclass(frozen=True)
class RhoEstimate:
    rho: float
    exact_score_log_loss: float
    observations: int
    low_score_observations: int
    candidates_evaluated: int


def dixon_coles_tau(
    home_goals: int,
    away_goals: int,
    home_expected: float,
    away_expected: float,
    rho: float,
) -> float:
    """Devuelve el factor tau definido por Dixon y Coles para 0/1 goles."""
    if not isfinite(rho):
        raise DixonColesError("rho must be finite.")
    if home_goals == 0 and away_goals == 0:
        return 1 - home_expected * away_expected * rho
    if home_goals == 0 and away_goals == 1:
        return 1 + home_expected * rho
    if home_goals == 1 and away_goals == 0:
        return 1 + away_expected * rho
    if home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1.0


def _poisson_probability(goals: int, expected: float) -> float:
    return exp(-expected) * expected**goals / factorial(goals)


def _exact_score_probability(
    observation: DixonColesObservation, rho: float
) -> float:
    correction = dixon_coles_tau(
        observation.home_goals,
        observation.away_goals,
        observation.home_expected_goals,
        observation.away_expected_goals,
        rho,
    )
    if correction <= 0:
        return 0.0
    return (
        _poisson_probability(
            observation.home_goals, observation.home_expected_goals
        )
        * _poisson_probability(
            observation.away_goals, observation.away_expected_goals
        )
        * correction
    )


def estimate_rho(
    observations: list[DixonColesObservation],
    *,
    minimum: float = -0.20,
    maximum: float = 0.20,
    step: float = 0.01,
) -> RhoEstimate:
    """Selecciona rho por menor Log Loss de marcadores exactos históricos."""
    if not observations:
        raise DixonColesError("At least one observation is required to estimate rho.")
    if not all(isfinite(value) for value in (minimum, maximum, step)):
        raise DixonColesError("The rho grid must contain finite values.")
    if minimum > maximum or step <= 0:
        raise DixonColesError("The rho grid requires minimum <= maximum and step > 0.")

    candidate_count = int(round((maximum - minimum) / step)) + 1
    candidates = [round(minimum + index * step, 10) for index in range(candidate_count)]
    best: tuple[float, float] | None = None
    candidates_evaluated = 0

    for rho in candidates:
        losses: list[float] = []
        for observation in observations:
            probability = _exact_score_probability(observation, rho)
            if probability <= 0 or not isfinite(probability):
                losses = []
                break
            losses.append(-log(probability))
        if not losses:
            continue
        candidates_evaluated += 1
        average_loss = sum(losses) / len(losses)
        # Si dos candidatos empatan, se conserva el rho más cercano a cero para
        # evitar una corrección innecesariamente intensa.
        candidate_key = (average_loss, abs(rho))
        if best is None or candidate_key < (best[1], abs(best[0])):
            best = (rho, average_loss)

    if best is None:
        raise DixonColesError("No rho candidate produced valid probabilities.")
    return RhoEstimate(
        rho=best[0],
        exact_score_log_loss=best[1],
        observations=len(observations),
        low_score_observations=sum(
            observation.home_goals <= 1 and observation.away_goals <= 1
            for observation in observations
        ),
        candidates_evaluated=candidates_evaluated,
    )


def apply_dixon_coles(
    poisson_prediction: dict[str, Any],
    *,
    rho: float,
    rho_training_matches: int,
    rho_training_cutoff: str,
) -> dict[str, Any]:
    """Corrige los cuatro marcadores bajos y sus probabilidades derivadas."""
    if not isfinite(rho):
        raise DixonColesError("rho must be finite.")
    if (
        isinstance(rho_training_matches, bool)
        or not isinstance(rho_training_matches, int)
        or rho_training_matches <= 0
    ):
        raise DixonColesError("rho_training_matches must be a positive integer.")
    matrix = poisson_prediction.get("score_matrix")
    if not isinstance(matrix, list) or not matrix:
        raise DixonColesError("The Poisson prediction requires a score matrix.")
    team_1_expected = poisson_prediction.get("estimated_team_1_goals")
    team_2_expected = poisson_prediction.get("estimated_team_2_goals")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value < 0
        for value in (team_1_expected, team_2_expected)
    ):
        raise DixonColesError("The Poisson prediction requires valid expected goals.")

    adjusted_matrix: list[dict[str, Any]] = []
    changes = {"team_1_win": 0.0, "draw": 0.0, "team_2_win": 0.0}
    both_score_change = 0.0
    total_change = 0.0
    for cell in matrix:
        team_1_goals = cell.get("team_1_goals")
        team_2_goals = cell.get("team_2_goals")
        probability = cell.get("probability")
        if (
            isinstance(team_1_goals, bool)
            or not isinstance(team_1_goals, int)
            or isinstance(team_2_goals, bool)
            or not isinstance(team_2_goals, int)
            or isinstance(probability, bool)
            or not isinstance(probability, (int, float))
        ):
            raise DixonColesError("The score matrix contains an invalid cell.")
        factor = dixon_coles_tau(
            team_1_goals,
            team_2_goals,
            float(team_1_expected),
            float(team_2_expected),
            rho,
        )
        if factor <= 0:
            raise DixonColesError("rho produces a non-positive score correction.")
        adjusted_probability = probability * factor
        change = adjusted_probability - probability
        total_change += change
        if team_1_goals > team_2_goals:
            changes["team_1_win"] += change
        elif team_1_goals < team_2_goals:
            changes["team_2_win"] += change
        else:
            changes["draw"] += change
        if team_1_goals > 0 and team_2_goals > 0:
            both_score_change += change
        adjusted_matrix.append({**cell, "probability": adjusted_probability})

    # La función tau conserva la masa total teóricamente. Esta comprobación
    # detecta matrices incompletas que no incluyan los cuatro marcadores bajos.
    if abs(total_change) > 1e-10:
        raise DixonColesError(
            "The Dixon-Coles adjustment did not conserve probability."
        )

    adjusted = {
        **poisson_prediction,
        "model_version": "dixon-coles-v0.1.0",
        "base_model_version": poisson_prediction.get("model_version"),
        "team_1_win_probability": poisson_prediction["team_1_win_probability"]
        + changes["team_1_win"],
        "draw_probability": poisson_prediction["draw_probability"] + changes["draw"],
        "team_2_win_probability": poisson_prediction["team_2_win_probability"]
        + changes["team_2_win"],
        "both_teams_score_probability": poisson_prediction[
            "both_teams_score_probability"
        ]
        + both_score_change,
        "score_matrix": adjusted_matrix,
        "top_scorelines": sorted(
            adjusted_matrix, key=lambda item: item["probability"], reverse=True
        )[:3],
        "dixon_coles": {
            "rho": rho,
            "rho_training_matches": rho_training_matches,
            "rho_training_cutoff": rho_training_cutoff,
            "adjusted_scorelines": ["0-0", "0-1", "1-0", "1-1"],
        },
    }
    return adjusted
