import argparse
import json
import os
import sys
from pathlib import Path

from backtesting.evaluator import BacktestError, run_temporal_backtest
from backtesting.reports import write_aggregate_reports
from data_repository import SQLiteDataRepository

API_DIRECTORY = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = API_DIRECTORY / "data" / "footballvs.db"
DEFAULT_OUTPUT_DIRECTORY = API_DIRECTORY / "backtesting" / "results"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run leakage-safe temporal backtesting with local SQLite data."
    )
    parser.add_argument("--competition", default="PL")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path(os.getenv("FOOTBALLVS_DB_PATH", DEFAULT_DATABASE_PATH)),
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT_DIRECTORY
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    repository = SQLiteDataRepository(arguments.database)
    repository.initialize()
    competition = next(
        (
            item
            for item in repository.list_documents("competition")
            if item.get("code") == arguments.competition.upper()
        ),
        None,
    )
    if competition is None:
        print("Competition is not synchronized.", file=sys.stderr)
        return 2
    try:
        result = run_temporal_backtest(
            repository.list_documents("match"),
            repository.list_documents("season"),
            competition_id=competition["id"],
        )
        write_aggregate_reports(result, arguments.output)
    except (BacktestError, OSError, ValueError) as error:
        print(f"Backtesting failed: {error}", file=sys.stderr)
        return 3

    print(
        json.dumps(
            {
                "competition_code": competition["code"],
                "selected_model": result["selection"]["selected_model"],
                "output_directory": str(arguments.output.resolve()),
                "seasons": [
                    {
                        "name": season["season_name"],
                        "coverage": season["coverage"],
                        "evaluated_matches": season["evaluated_matches"],
                    }
                    for season in result["seasons"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
