import argparse
import json
import os
import sys
from pathlib import Path

from data_repository import SQLiteDataRepository
from elo_rating import EloParameters, EloRatingError, calculate_elo_history

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "footballvs.db"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate chronological Elo ratings from normalized SQLite matches."
        )
    )
    parser.add_argument("--competition", default="PL")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path(os.getenv("FOOTBALLVS_DB_PATH", DEFAULT_DATABASE_PATH)),
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

    parameters = EloParameters()
    try:
        history, current_ratings = calculate_elo_history(
            repository.list_documents("match"),
            repository.list_documents("season"),
            competition_id=competition["id"],
            parameters=parameters,
        )
        repository.upsert_many("elo_history", history)
        repository.upsert_many("elo_rating", current_ratings)
    except (EloRatingError, OSError, ValueError) as error:
        print(f"Elo calculation failed: {error}", file=sys.stderr)
        return 3

    print(
        json.dumps(
            {
                "competition_code": competition["code"],
                "model_version": parameters.model_version,
                "history_records_processed": len(history),
                "history_records_stored_total": repository.count("elo_history"),
                "current_ratings_processed": len(current_ratings),
                "current_ratings_stored_total": repository.count("elo_rating"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
