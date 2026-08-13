from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from math import exp, factorial
from typing import Any

from backtesting.elo_evaluator import run_elo_grid_backtest
from backtesting.metrics import MetricsAccumulator, Outcome
from dixon_coles import (
    DixonColesObservation,
    RhoEstimate,
    apply_dixon_coles,
    dixon_coles_tau,
    estimate_rho,
)
from poisson_model import (
    InsufficientPoissonDataError,
    PoissonParameters,
    predict_poisson,
)


class BacktestError(ValueError):
    """Indica una configuración o muestra temporal inválida."""


@dataclass(frozen=True)
class BacktestParameters:
    target_season_names: tuple[str, ...] = ("2024/25", "2025/26")
    minimum_coverage: float = 0.80
    minimum_relative_improvement: float = 0.01
    maximum_season_regression: float = 0.01
    probability_epsilon: float = 0.000001

    def __post_init__(self) -> None:
        if not self.target_season_names:
            raise BacktestError("At least one target season is required.")
        if not 0 < self.minimum_coverage <= 1:
            raise BacktestError("minimum_coverage must be between zero and one.")
        if self.minimum_relative_improvement < 0:
            raise BacktestError("minimum_relative_improvement cannot be negative.")
        if self.maximum_season_regression < 0:
            raise BacktestError("maximum_season_regression cannot be negative.")
        if not 0 < self.probability_epsilon < 0.5:
            raise BacktestError("probability_epsilon must be between zero and 0.5.")


def _text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BacktestError(f"{field} must be non-empty text.")
    return value.strip()


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise BacktestError("utc_date must be an ISO timestamp.") from error
    if parsed.tzinfo is None:
        raise BacktestError("utc_date must include a timezone.")
    return parsed.astimezone(UTC)


def _score(match: dict[str, Any]) -> tuple[int, int]:
    home = match.get("home_score")
    away = match.get("away_score")
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (home, away)
    ):
        raise BacktestError("Finished matches require integer scores.")
    return home, away


def _outcome(home_goals: int, away_goals: int) -> Outcome:
    if home_goals > away_goals:
        return "team_1_win"
    if home_goals < away_goals:
        return "team_2_win"
    return "draw"


def _probabilities(prediction: dict[str, Any]) -> dict[Outcome, float]:
    return {
        "team_1_win": prediction["team_1_win_probability"],
        "draw": prediction["draw_probability"],
        "team_2_win": prediction["team_2_win_probability"],
    }


def _poisson_exact(
    home_goals: int, away_goals: int, prediction: dict[str, Any]
) -> float:
    home_expected = prediction["estimated_team_1_goals"]
    away_expected = prediction["estimated_team_2_goals"]
    return (
        exp(-home_expected) * home_expected**home_goals / factorial(home_goals)
        * exp(-away_expected)
        * away_expected**away_goals
        / factorial(away_goals)
    )


def _dixon_coles_exact(
    home_goals: int, away_goals: int, prediction: dict[str, Any], rho: float
) -> float:
    return _poisson_exact(home_goals, away_goals, prediction) * dixon_coles_tau(
        home_goals,
        away_goals,
        prediction["estimated_team_1_goals"],
        prediction["estimated_team_2_goals"],
        rho,
    )


def _finished_matches(
    matches: list[dict[str, Any]], competition_id: str, season_id: str
) -> list[dict[str, Any]]:
    return sorted(
        (
            match
            for match in matches
            if match.get("competition_id") == competition_id
            and match.get("season_id") == season_id
            and match.get("status") == "FINISHED"
        ),
        key=lambda match: (_text(match, "utc_date"), _text(match, "id")),
    )


def _rho_training_observations(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    target_season: dict[str, Any],
    poisson_parameters: PoissonParameters,
) -> tuple[list[DixonColesObservation], Counter[str]]:
    target_start = _text(target_season, "start_date")
    prior_seasons = sorted(
        (
            season
            for season in seasons
            if season.get("competition_id") == competition_id
            and _text(season, "end_date") < target_start
        ),
        key=lambda season: (_text(season, "start_date"), _text(season, "id")),
    )
    observations: list[DixonColesObservation] = []
    exclusions: Counter[str] = Counter()
    for season in prior_seasons:
        season_id = _text(season, "id")
        for match in _finished_matches(matches, competition_id, season_id):
            cutoff = _timestamp(_text(match, "utc_date"))
            try:
                prediction = predict_poisson(
                    matches,
                    seasons,
                    competition_id=competition_id,
                    season_id=season_id,
                    team_1_id=_text(match, "home_team_id"),
                    team_2_id=_text(match, "away_team_id"),
                    venue="team1",
                    input_data_cutoff=cutoff,
                    calculated_at=cutoff,
                    parameters=poisson_parameters,
                )
            except InsufficientPoissonDataError:
                exclusions["insufficient_rho_training_data"] += 1
                continue
            home_goals, away_goals = _score(match)
            if _poisson_exact(home_goals, away_goals, prediction) <= 0:
                # rho sólo corrige dependencia en marcadores bajos; no puede
                # reparar una tasa Poisson cero para un gol observado.
                exclusions["zero_probability_rho_observation"] += 1
                continue
            observations.append(
                DixonColesObservation(
                    prediction["estimated_team_1_goals"],
                    prediction["estimated_team_2_goals"],
                    home_goals,
                    away_goals,
                    match_id=_text(match, "id"),
                )
            )
    return observations, exclusions


def _evaluate_season(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    season: dict[str, Any],
    rho_estimate: RhoEstimate,
    poisson_parameters: PoissonParameters,
    config: BacktestParameters,
) -> dict[str, Any]:
    target_matches = _finished_matches(matches, competition_id, _text(season, "id"))
    poisson_metrics = MetricsAccumulator()
    dixon_coles_metrics = MetricsAccumulator()
    exclusions: Counter[str] = Counter()
    for match in target_matches:
        cutoff = _timestamp(_text(match, "utc_date"))
        try:
            poisson = predict_poisson(
                matches,
                seasons,
                competition_id=competition_id,
                season_id=_text(season, "id"),
                team_1_id=_text(match, "home_team_id"),
                team_2_id=_text(match, "away_team_id"),
                venue="team1",
                input_data_cutoff=cutoff,
                calculated_at=cutoff,
                parameters=poisson_parameters,
            )
        except InsufficientPoissonDataError:
            exclusions["insufficient_data"] += 1
            continue
        adjusted = apply_dixon_coles(
            poisson,
            rho=rho_estimate.rho,
            rho_training_matches=rho_estimate.observations,
            rho_training_cutoff=f"{_text(season, 'start_date')}T00:00:00Z",
        )
        home_goals, away_goals = _score(match)
        outcome = _outcome(home_goals, away_goals)
        poisson_metrics.record(
            _probabilities(poisson),
            outcome,
            _poisson_exact(home_goals, away_goals, poisson),
            epsilon=config.probability_epsilon,
        )
        dixon_coles_metrics.record(
            _probabilities(adjusted),
            outcome,
            _dixon_coles_exact(home_goals, away_goals, poisson, rho_estimate.rho),
            epsilon=config.probability_epsilon,
        )
    evaluated = poisson_metrics.observations
    total = len(target_matches)
    result = {
        "season_id": _text(season, "id"),
        "season_name": _text(season, "name"),
        "total_finished_matches": total,
        "evaluated_matches": evaluated,
        "coverage": evaluated / total if total else 0.0,
        "excluded_matches": total - evaluated,
        "exclusion_reasons": dict(sorted(exclusions.items())),
        "rho": asdict(rho_estimate),
        "poisson": poisson_metrics.summary(),
        "dixon_coles": dixon_coles_metrics.summary(),
        "_poisson_totals": poisson_metrics.totals(),
        "_dixon_coles_totals": dixon_coles_metrics.totals(),
    }
    return result


def _global_metrics(
    season_results: list[dict[str, Any]], key: str
) -> dict[str, float | int]:
    combined = MetricsAccumulator()
    for result in season_results:
        totals = result[f"_{key}_totals"]
        combined.observations += totals["observations"]
        combined.outcome_log_loss_total += totals["outcome_log_loss_total"]
        combined.brier_total += totals["brier_total"]
        combined.exact_score_log_loss_total += totals["exact_score_log_loss_total"]
        combined.correct_predictions += totals["correct_predictions"]
    return combined.summary()


def _selection(
    season_results: list[dict[str, Any]],
    poisson_global: dict[str, float | int],
    dixon_coles_global: dict[str, float | int],
    config: BacktestParameters,
) -> dict[str, Any]:
    poisson_loss = float(poisson_global["outcome_log_loss"])
    dixon_loss = float(dixon_coles_global["outcome_log_loss"])
    relative_improvement = (
        (poisson_loss - dixon_loss) / poisson_loss if poisson_loss else 0.0
    )
    coverage_passed = all(
        result["coverage"] >= config.minimum_coverage for result in season_results
    )
    season_stability_passed = all(
        result["dixon_coles"]["outcome_log_loss"]
        <= result["poisson"]["outcome_log_loss"]
        * (1 + config.maximum_season_regression)
        for result in season_results
    )
    exact_score_passed = (
        dixon_coles_global["exact_score_log_loss"]
        < poisson_global["exact_score_log_loss"]
    )
    improvement_passed = relative_improvement >= config.minimum_relative_improvement
    selected = all(
        (
            coverage_passed,
            season_stability_passed,
            exact_score_passed,
            improvement_passed,
        )
    )
    return {
        "selected_model": "dixon-coles-v0.1.0" if selected else "poisson-v0.1.0",
        "dixon_coles_selected": selected,
        "relative_outcome_log_loss_improvement": relative_improvement,
        "checks": {
            "minimum_coverage": coverage_passed,
            "maximum_season_regression": season_stability_passed,
            "exact_score_log_loss_improved": exact_score_passed,
            "minimum_relative_improvement": improvement_passed,
        },
    }


def run_temporal_backtest(
    matches: list[dict[str, Any]],
    seasons: list[dict[str, Any]],
    *,
    competition_id: str,
    parameters: BacktestParameters | None = None,
    poisson_parameters: PoissonParameters | None = None,
) -> dict[str, Any]:
    """Evalúa partidos en orden temporal sin conservar registros individuales."""
    config = parameters or BacktestParameters()
    poisson_config = poisson_parameters or PoissonParameters()
    season_by_name = {
        _text(season, "name"): season
        for season in seasons
        if season.get("competition_id") == competition_id
    }
    missing = [
        name for name in config.target_season_names if name not in season_by_name
    ]
    if missing:
        raise BacktestError(f"Missing target seasons: {', '.join(missing)}")

    results: list[dict[str, Any]] = []
    training_exclusions: Counter[str] = Counter()
    for season_name in config.target_season_names:
        season = season_by_name[season_name]
        observations, exclusions = _rho_training_observations(
            matches,
            seasons,
            competition_id=competition_id,
            target_season=season,
            poisson_parameters=poisson_config,
        )
        training_exclusions.update(exclusions)
        if not observations:
            raise BacktestError(
                f"Season {season_name} has no eligible prior observations for rho."
            )
        rho_estimate = estimate_rho(observations)
        results.append(
            _evaluate_season(
                matches,
                seasons,
                competition_id=competition_id,
                season=season,
                rho_estimate=rho_estimate,
                poisson_parameters=poisson_config,
                config=config,
            )
        )

    poisson_global = _global_metrics(results, "poisson")
    dixon_coles_global = _global_metrics(results, "dixon_coles")
    for result in results:
        del result["_poisson_totals"]
        del result["_dixon_coles_totals"]
    result = {
        "backtest_version": "temporal-backtest-v0.1.0",
        "competition_id": competition_id,
        "parameters": asdict(config),
        "poisson_parameters": asdict(poisson_config),
        "seasons": results,
        "global": {
            "poisson": poisson_global,
            "dixon_coles": dixon_coles_global,
        },
        "rho_training_exclusions": dict(sorted(training_exclusions.items())),
        "selection": _selection(
            results, poisson_global, dixon_coles_global, config
        ),
    }
    result["elo"] = run_elo_grid_backtest(
        matches,
        seasons,
        competition_id=competition_id,
        target_season_names=config.target_season_names,
        minimum_relative_improvement=config.minimum_relative_improvement,
    )
    return result
