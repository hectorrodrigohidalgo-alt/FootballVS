from dataclasses import asdict, dataclass
from itertools import product
from statistics import fmean
from typing import Any

from elo_rating import EloParameters, calculate_elo_history


@dataclass
class EloMetrics:
    observations: int = 0
    squared_error_total: float = 0.0
    absolute_error_total: float = 0.0
    decisive_matches: int = 0
    decisive_correct: int = 0
    absolute_change_total: float = 0.0

    def record(
        self, expected: float, actual: float, rating_change: float
    ) -> None:
        error = expected - actual
        self.observations += 1
        self.squared_error_total += error**2
        self.absolute_error_total += abs(error)
        self.absolute_change_total += abs(rating_change)
        if actual != 0.5:
            self.decisive_matches += 1
            self.decisive_correct += (expected > 0.5) == (actual == 1.0)

    def summary(self) -> dict[str, float | int]:
        return {
            "evaluated_matches": self.observations,
            "mean_squared_error": self.squared_error_total / self.observations,
            "mean_absolute_error": self.absolute_error_total / self.observations,
            "decisive_accuracy": (
                self.decisive_correct / self.decisive_matches
                if self.decisive_matches
                else 0.0
            ),
            "mean_absolute_rating_change": (
                self.absolute_change_total / self.observations
            ),
        }


def elo_parameter_grid() -> list[EloParameters]:
    """Genera las 180 combinaciones acordadas en orden determinista."""
    return [
        EloParameters(
            model_version="elo-backtest-v0.1.0",
            k_factor=k_factor,
            home_advantage=home_advantage,
            season_retention=season_retention,
            promoted_rating=promoted_rating,
        )
        for k_factor, home_advantage, season_retention, promoted_rating in product(
            (10.0, 20.0, 30.0, 40.0),
            (0.0, 40.0, 65.0, 80.0, 100.0),
            (0.5, 0.75, 1.0),
            (1400.0, 1450.0, 1500.0),
        )
    ]


def _evaluate_configuration(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    competition_id: str,
    target_season_names: tuple[str, ...],
    parameters: EloParameters,
) -> dict[str, Any]:
    history, _ = calculate_elo_history(
        matches, seasons, competition_id=competition_id, parameters=parameters
    )
    season_names = {
        season["id"]: season["name"]
        for season in seasons
        if season.get("competition_id") == competition_id
    }
    metrics = {name: EloMetrics() for name in target_season_names}
    # Cada encuentro tiene dos registros; el registro local contiene la
    # probabilidad y el resultado desde la perspectiva evaluada.
    for record in history:
        season_name = season_names.get(record["season_id"])
        if season_name not in metrics or record["venue"] != "home":
            continue
        metrics[season_name].record(
            record["expected_score"],
            record["actual_score"],
            record["rating_change"],
        )
    summaries = {name: value.summary() for name, value in metrics.items()}
    return {
        "parameters": asdict(parameters),
        "seasons": summaries,
        "average_mean_squared_error": fmean(
            float(summary["mean_squared_error"]) for summary in summaries.values()
        ),
        "average_mean_absolute_error": fmean(
            float(summary["mean_absolute_error"]) for summary in summaries.values()
        ),
        "average_mean_absolute_rating_change": fmean(
            float(summary["mean_absolute_rating_change"])
            for summary in summaries.values()
        ),
    }


def _parameter_distance(candidate: dict[str, Any], baseline: EloParameters) -> float:
    return (
        abs(candidate["k_factor"] - baseline.k_factor) / 10
        + abs(candidate["home_advantage"] - baseline.home_advantage) / 20
        + abs(candidate["season_retention"] - baseline.season_retention) / 0.25
        + abs(candidate["promoted_rating"] - baseline.promoted_rating) / 50
    )


def run_elo_grid_backtest(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    target_season_names: tuple[str, ...] = ("2024/25", "2025/26"),
    minimum_relative_improvement: float = 0.01,
) -> dict[str, Any]:
    """Evalúa la cuadrícula Elo y aplica la regla conservadora del 1%."""
    baseline_parameters = EloParameters()
    results = [
        _evaluate_configuration(
            matches,
            seasons,
            competition_id,
            target_season_names,
            parameters,
        )
        for parameters in elo_parameter_grid()
    ]
    baseline = next(
        result
        for result in results
        if all(
            result["parameters"][field] == getattr(baseline_parameters, field)
            for field in (
                "k_factor",
                "home_advantage",
                "season_retention",
                "promoted_rating",
            )
        )
    )
    best = min(
        results,
        key=lambda result: (
            result["average_mean_squared_error"],
            result["average_mean_absolute_error"],
            result["average_mean_absolute_rating_change"],
            _parameter_distance(result["parameters"], baseline_parameters),
        ),
    )
    baseline_error = baseline["average_mean_squared_error"]
    relative_improvement = (
        (baseline_error - best["average_mean_squared_error"]) / baseline_error
        if baseline_error
        else 0.0
    )
    improves_each_season = all(
        best["seasons"][name]["mean_squared_error"]
        < baseline["seasons"][name]["mean_squared_error"]
        for name in target_season_names
    )
    selected_best = (
        relative_improvement >= minimum_relative_improvement
        and improves_each_season
    )
    selected = best if selected_best else baseline
    return {
        "grid_size": len(results),
        "target_seasons": list(target_season_names),
        "selection_rule": {
            "minimum_relative_improvement": minimum_relative_improvement,
            "must_improve_every_season": True,
        },
        "baseline": baseline,
        "best_candidate": best,
        "relative_improvement": relative_improvement,
        "improves_every_season": improves_each_season,
        "baseline_replaced": selected_best,
        "selected": selected,
    }
