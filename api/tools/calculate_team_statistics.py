import argparse
import json
import os
import sys
from pathlib import Path

from data_repository import SQLiteDataRepository
from team_statistics import TeamStatisticsError, calculate_team_snapshots

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "footballvs.db"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate team statistics from normalized SQLite matches."
    )
    parser.add_argument("--competition", default="PL")
    parser.add_argument("--season", type=int, default=2026)
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

    competitions = repository.list_documents("competition")
    seasons = repository.list_documents("season")
    competition = next(
        (
            item
            for item in competitions
            if item.get("code") == arguments.competition.upper()
        ),
        None,
    )
    season = next(
        (
            item
            for item in seasons
            if item.get("competition_id") == (competition or {}).get("id")
            and str(item.get("start_date", "")).startswith(str(arguments.season))
        ),
        None,
    )
    if competition is None or season is None:
        print("Competition or season is not synchronized.", file=sys.stderr)
        return 2

    try:
        snapshots = calculate_team_snapshots(
            repository.list_documents("match"),
            competition_id=competition["id"],
            season_id=season["id"],
        )
        repository.upsert_many("team_snapshot", snapshots)
    except (TeamStatisticsError, OSError, ValueError) as error:
        print(f"Statistics calculation failed: {error}", file=sys.stderr)
        return 3

    print(
        json.dumps(
            {
                "competition_code": competition["code"],
                "season": season["name"],
                "snapshots_processed": len(snapshots),
                "snapshots_stored_total": repository.count("team_snapshot"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
