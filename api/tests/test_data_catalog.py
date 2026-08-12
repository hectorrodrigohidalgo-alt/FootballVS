from pathlib import Path

from data_catalog import RepositoryDataCatalog, create_data_catalog
from data_repository import SQLiteDataRepository


def repository_catalog(tmp_path: Path) -> RepositoryDataCatalog:
    repository = SQLiteDataRepository(tmp_path / "footballvs.db")
    repository.initialize()
    repository.upsert_many(
        "competition",
        [
            {
                "id": "football-data:competition:2021",
                "code": "PL",
                "name": "Premier League",
                "country": "England",
                "current_season_id": "football-data:season:2403",
            }
        ],
    )
    repository.upsert_many(
        "season",
        [
            {
                "id": "football-data:season:2403",
                "competition_id": "football-data:competition:2021",
                "name": "2026/27",
            }
        ],
    )
    repository.upsert_many(
        "team",
        [
            {
                "id": "football-data:team:57",
                "name": "Arsenal FC",
                "short_name": "Arsenal",
                "tla": "ARS",
            },
            {
                "id": "football-data:team:64",
                "name": "Liverpool FC",
                "short_name": "Liverpool",
                "tla": "LIV",
            },
            {
                "id": "football-data:team:999",
                "name": "Historical FC",
                "short_name": "Historical",
                "tla": "HIS",
            },
        ],
    )
    repository.upsert_many(
        "match",
        [
            {
                "id": "football-data:match:1",
                "competition_id": "football-data:competition:2021",
                "season_id": "football-data:season:2403",
                "home_team_id": "football-data:team:57",
                "away_team_id": "football-data:team:64",
            }
        ],
    )
    return RepositoryDataCatalog(repository)


def test_repository_catalog_exposes_public_competition_contract(tmp_path: Path) -> None:
    catalog = repository_catalog(tmp_path)

    assert catalog.list_competitions() == [
        {
            "id": "PL",
            "name": "Premier League",
            "country": "England",
            "season": "2026/27",
        }
    ]


def test_repository_catalog_lists_only_current_season_teams(tmp_path: Path) -> None:
    catalog = repository_catalog(tmp_path)

    teams = catalog.list_teams("PL")

    assert teams is not None
    assert [team["name"] for team in teams] == ["Arsenal FC", "Liverpool FC"]
    assert all(team["name"] != "Historical FC" for team in teams)


def test_repository_catalog_returns_none_for_unknown_competition(
    tmp_path: Path,
) -> None:
    assert repository_catalog(tmp_path).list_teams("UCL") is None


def test_catalog_factory_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("APP_DATA_SOURCE", raising=False)

    assert create_data_catalog().source == "mock"
