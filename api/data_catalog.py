import os
from pathlib import Path
from typing import Any, Protocol

from data_repository import SQLiteDataRepository
from mock_data import COMPETITION, team_summaries

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "data" / "footballvs.db"


class DataCatalog(Protocol):
    """Lecturas necesarias para poblar los selectores del frontend."""

    @property
    def source(self) -> str: ...

    def list_competitions(self) -> list[dict[str, Any]]: ...

    def list_teams(self, competition_code: str) -> list[dict[str, Any]] | None: ...


class MockDataCatalog:
    """Mantiene disponible el contrato ficticio para CI y pruebas aisladas."""

    source = "mock"

    def list_competitions(self) -> list[dict[str, Any]]:
        return [COMPETITION]

    def list_teams(self, competition_code: str) -> list[dict[str, Any]] | None:
        if competition_code != COMPETITION["id"]:
            return None
        return team_summaries()


class RepositoryDataCatalog:
    """Construye el catálogo público desde documentos normalizados."""

    source = "repository"

    def __init__(self, repository: SQLiteDataRepository) -> None:
        self._repository = repository

    def _competition(self, competition_code: str) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in self._repository.list_documents("competition")
                if item.get("code") == competition_code
            ),
            None,
        )

    def _season(self, season_id: str | None) -> dict[str, Any] | None:
        if not season_id:
            return None
        return next(
            (
                item
                for item in self._repository.list_documents("season")
                if item.get("id") == season_id
            ),
            None,
        )

    def list_competitions(self) -> list[dict[str, Any]]:
        result = []
        for competition in self._repository.list_documents("competition"):
            season = self._season(competition.get("current_season_id"))
            result.append(
                {
                    # El código oficial sigue siendo el ID público para conservar
                    # URLs breves como /competitions/PL/teams.
                    "id": competition["code"],
                    "name": competition["name"],
                    "country": competition["country"],
                    "season": season["name"] if season else None,
                }
            )
        return sorted(result, key=lambda item: item["name"])

    def list_teams(self, competition_code: str) -> list[dict[str, Any]] | None:
        competition = self._competition(competition_code)
        if competition is None:
            return None

        current_season_id = competition.get("current_season_id")
        team_ids = {
            team_id
            for match in self._repository.list_documents("match")
            if match.get("competition_id") == competition.get("id")
            and match.get("season_id") == current_season_id
            for team_id in (match.get("home_team_id"), match.get("away_team_id"))
            if isinstance(team_id, str)
        }
        teams = [
            {
                "id": team["id"],
                "name": team["name"],
                "short_name": team["short_name"],
                "tla": team["tla"],
            }
            for team in self._repository.list_documents("team")
            if team.get("id") in team_ids
        ]
        return sorted(teams, key=lambda item: item["name"])


def create_data_catalog() -> DataCatalog:
    """Selecciona la fuente sin acoplar los endpoints a SQLite."""
    source = os.getenv("APP_DATA_SOURCE", "mock").strip().lower()
    if source == "mock":
        return MockDataCatalog()
    if source == "repository":
        database_path = Path(os.getenv("FOOTBALLVS_DB_PATH", DEFAULT_DATABASE_PATH))
        repository = SQLiteDataRepository(database_path)
        repository.initialize()
        return RepositoryDataCatalog(repository)
    raise ValueError("APP_DATA_SOURCE must be mock or repository.")
