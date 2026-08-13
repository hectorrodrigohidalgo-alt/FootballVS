import json
from datetime import UTC, datetime, timedelta

import pytest

from backtesting.evaluator import (
    BacktestError,
    BacktestParameters,
    run_temporal_backtest,
)
from backtesting.metrics import (
    MetricsAccumulator,
    MetricsError,
    normalize_probabilities,
)
from backtesting.reports import render_markdown_report, write_aggregate_reports
from poisson_model import PoissonParameters

COMPETITION = "competition:pl"
TEAM_A = "team:a"
TEAM_B = "team:b"


def season(identifier: str, name: str, year: int) -> dict:
    return {
        "id": identifier,
        "competition_id": COMPETITION,
        "name": name,
        "start_date": f"{year}-08-01",
        "end_date": f"{year + 1}-05-31",
    }


def season_matches(season_id: str, year: int, *, total: int = 8) -> list[dict]:
    start = datetime(year, 8, 2, 12, tzinfo=UTC)
    scores = ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (2, 0), (0, 2))
    return [
        {
            "id": f"match:{season_id}:{index}",
            "competition_id": COMPETITION,
            "season_id": season_id,
            "utc_date": (start + timedelta(days=index)).isoformat().replace(
                "+00:00", "Z"
            ),
            "status": "FINISHED",
            "home_team_id": TEAM_A,
            "away_team_id": TEAM_B,
            "home_score": scores[index % len(scores)][0],
            "away_score": scores[index % len(scores)][1],
        }
        for index in range(total)
    ]


def lightweight_poisson() -> PoissonParameters:
    return PoissonParameters(
        minimum_venue_matches=1,
        minimum_neutral_matches=1,
        minimum_league_matches=1,
    )


def test_metrics_clip_normalize_and_accumulate() -> None:
    normalized = normalize_probabilities(
        {"team_1_win": 0.0, "draw": 0.25, "team_2_win": 0.75}
    )
    assert sum(normalized.values()) == pytest.approx(1)
    assert normalized["team_1_win"] > 0

    accumulator = MetricsAccumulator()
    accumulator.record(
        {"team_1_win": 0.6, "draw": 0.2, "team_2_win": 0.2},
        "team_1_win",
        0.1,
    )
    summary = accumulator.summary()
    assert summary["evaluated_matches"] == 1
    assert summary["outcome_log_loss"] == pytest.approx(0.5108256)
    assert summary["outcome_accuracy"] == 1

    with pytest.raises(MetricsError, match="three"):
        normalize_probabilities({"draw": 1.0})  # type: ignore[arg-type]


def test_runs_temporal_backtest_with_aggregate_results_only() -> None:
    prior = season("season:prior", "2023/24", 2023)
    target = season("season:target", "2024/25", 2024)
    matches = [
        *season_matches(prior["id"], 2023),
        *season_matches(target["id"], 2024),
    ]

    result = run_temporal_backtest(
        matches,
        [prior, target],
        competition_id=COMPETITION,
        parameters=BacktestParameters(target_season_names=("2024/25",)),
        poisson_parameters=lightweight_poisson(),
    )

    evaluated = result["seasons"][0]
    assert result["backtest_version"] == "temporal-backtest-v0.1.0"
    assert evaluated["coverage"] == pytest.approx(1)
    assert evaluated["rho"]["observations"] == 5
    assert result["rho_training_exclusions"] == {
        "insufficient_rho_training_data": 1,
        "zero_probability_rho_observation": 2,
    }
    assert result["global"]["poisson"]["evaluated_matches"] == 8
    assert result["global"]["dixon_coles"]["evaluated_matches"] == 8
    assert result["elo"]["grid_size"] == 180
    assert set(result["elo"]["selected"]["seasons"]) == {"2024/25"}
    assert "match:" not in json.dumps(result)
    assert set(result["selection"]["checks"]) == {
        "minimum_coverage",
        "maximum_season_regression",
        "exact_score_log_loss_improved",
        "minimum_relative_improvement",
    }


def test_records_insufficient_target_matches_without_inventing_probabilities() -> None:
    prior = season("season:prior", "2023/24", 2023)
    target = season("season:target", "2024/25", 2024)
    target_matches = [
        {**match, "home_team_id": "team:c", "away_team_id": "team:d"}
        for match in season_matches(target["id"], 2024)
    ]
    matches = [*season_matches(prior["id"], 2023), *target_matches]

    result = run_temporal_backtest(
        matches,
        [prior, target],
        competition_id=COMPETITION,
        parameters=BacktestParameters(target_season_names=("2024/25",)),
        poisson_parameters=lightweight_poisson(),
    )

    evaluated = result["seasons"][0]
    # El primer partido no tiene antecedentes; desde el segundo el modelo ya
    # puede incorporar sólo los resultados anteriores de la misma temporada.
    assert evaluated["coverage"] == pytest.approx(7 / 8)
    assert evaluated["excluded_matches"] == 1
    assert evaluated["exclusion_reasons"] == {"insufficient_data": 1}
    assert result["selection"]["checks"]["minimum_coverage"] is True


def test_requires_every_configured_target_season() -> None:
    prior = season("season:prior", "2023/24", 2023)
    with pytest.raises(BacktestError, match="Missing target seasons"):
        run_temporal_backtest(
            season_matches(prior["id"], 2023),
            [prior],
            competition_id=COMPETITION,
        )


def test_writes_json_and_markdown_without_individual_matches(tmp_path) -> None:
    result = {
        "backtest_version": "temporal-backtest-v0.1.0",
        "competition_id": COMPETITION,
        "seasons": [
            {
                "season_name": "2024/25",
                "coverage": 0.9,
                "rho": {"rho": -0.08, "observations": 200},
                "poisson": {
                    "outcome_log_loss": 1.0,
                    "brier_score": 0.6,
                    "exact_score_log_loss": 2.8,
                    "outcome_accuracy": 0.5,
                },
                "dixon_coles": {
                    "outcome_log_loss": 0.98,
                    "brier_score": 0.59,
                    "exact_score_log_loss": 2.7,
                    "outcome_accuracy": 0.51,
                },
            }
        ],
        "selection": {
            "selected_model": "dixon-coles-v0.1.0",
            "relative_outcome_log_loss_improvement": 0.02,
            "checks": {"minimum_coverage": True},
        },
    }

    write_aggregate_reports(result, tmp_path)

    json_result = json.loads((tmp_path / "backtest-summary.json").read_text("utf-8"))
    markdown = (tmp_path / "backtest-summary.md").read_text("utf-8")
    assert json_result["competition_id"] == COMPETITION
    assert "Dixon-Coles" in markdown
    assert "registros individuales" in markdown
    assert render_markdown_report(result) == markdown
