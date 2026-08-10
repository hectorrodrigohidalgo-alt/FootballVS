import argparse
import json
import os
import sys
from pathlib import Path

from data_normalizer import FootballDataNormalizationError
from data_repository import SQLiteDataRepository
from data_sync import synchronize_competition_season
from football_data_client import (
    FootballDataClient,
    FootballDataConfigurationError,
    FootballDataRequestError,
)
from tools.validate_football_data import load_local_configuration

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "footballvs.db"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize one football-data.org season into local SQLite."
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
    try:
        api_key, base_url = load_local_configuration(
            Path(__file__).resolve().parents[1] / "local.settings.json"
        )
        repository = SQLiteDataRepository(arguments.database)
        repository.initialize()
        result = synchronize_competition_season(
            FootballDataClient(api_key=api_key, base_url=base_url),
            repository,
            competition_code=arguments.competition,
            season_start_year=arguments.season,
        )
        # Estos totales permiten comprobar que una segunda ejecución actualiza
        # los mismos documentos en vez de multiplicarlos.
        result["stored_totals"] = {
            entity_type: repository.count(entity_type)
            for entity_type in ("competition", "season", "team", "match")
        }
    except (
        FootballDataConfigurationError,
        FootballDataNormalizationError,
        FootballDataRequestError,
        OSError,
        ValueError,
    ) as error:
        print(f"Synchronization failed: {error}", file=sys.stderr)
        return 2

    # El resumen evita imprimir respuestas crudas, credenciales o rutas locales.
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
