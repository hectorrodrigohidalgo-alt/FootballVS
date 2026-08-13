from dataclasses import asdict, dataclass
from math import isfinite, log
from typing import Literal

Outcome = Literal["team_1_win", "draw", "team_2_win"]
OUTCOMES: tuple[Outcome, ...] = ("team_1_win", "draw", "team_2_win")


class MetricsError(ValueError):
    """Indica probabilidades o resultados incompatibles con la evaluación."""


@dataclass
class MetricsAccumulator:
    """Acumula métricas sin conservar registros de partidos del proveedor."""

    observations: int = 0
    outcome_log_loss_total: float = 0.0
    brier_total: float = 0.0
    exact_score_log_loss_total: float = 0.0
    correct_predictions: int = 0

    def record(
        self,
        probabilities: dict[Outcome, float],
        actual_outcome: Outcome,
        exact_score_probability: float,
        *,
        epsilon: float = 0.000001,
    ) -> None:
        normalized = normalize_probabilities(probabilities, epsilon=epsilon)
        exact_probability = clip_probability(exact_score_probability, epsilon)
        self.observations += 1
        self.outcome_log_loss_total += -log(normalized[actual_outcome])
        self.exact_score_log_loss_total += -log(exact_probability)
        self.brier_total += sum(
            (normalized[outcome] - (1.0 if outcome == actual_outcome else 0.0))
            ** 2
            for outcome in OUTCOMES
        )
        predicted = max(OUTCOMES, key=lambda outcome: normalized[outcome])
        self.correct_predictions += predicted == actual_outcome

    def summary(self) -> dict[str, float | int]:
        if self.observations == 0:
            return {
                "evaluated_matches": 0,
                "outcome_log_loss": 0.0,
                "brier_score": 0.0,
                "exact_score_log_loss": 0.0,
                "outcome_accuracy": 0.0,
            }
        return {
            "evaluated_matches": self.observations,
            "outcome_log_loss": self.outcome_log_loss_total / self.observations,
            "brier_score": self.brier_total / self.observations,
            "exact_score_log_loss": (
                self.exact_score_log_loss_total / self.observations
            ),
            "outcome_accuracy": self.correct_predictions / self.observations,
        }

    def totals(self) -> dict[str, float | int]:
        return asdict(self)


def clip_probability(probability: float, epsilon: float = 0.000001) -> float:
    if (
        isinstance(probability, bool)
        or not isinstance(probability, (int, float))
        or not isfinite(probability)
    ):
        raise MetricsError("Probabilities must be finite numeric values.")
    if not 0 < epsilon < 0.5:
        raise MetricsError("epsilon must be between zero and 0.5.")
    return min(1 - epsilon, max(epsilon, float(probability)))


def normalize_probabilities(
    probabilities: dict[Outcome, float], *, epsilon: float = 0.000001
) -> dict[Outcome, float]:
    if set(probabilities) != set(OUTCOMES):
        raise MetricsError("Exactly three 1X2 probabilities are required.")
    clipped = {
        outcome: clip_probability(probabilities[outcome], epsilon)
        for outcome in OUTCOMES
    }
    total = sum(clipped.values())
    return {outcome: clipped[outcome] / total for outcome in OUTCOMES}

