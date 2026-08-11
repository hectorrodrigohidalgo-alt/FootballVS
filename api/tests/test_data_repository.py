from pathlib import Path

import pytest

from data_repository import SQLiteDataRepository


@pytest.fixture
def repository(tmp_path: Path) -> SQLiteDataRepository:
    result = SQLiteDataRepository(tmp_path / "footballvs.db")
    result.initialize()
    return result


def test_upsert_repeated_document_does_not_duplicate_it(
    repository: SQLiteDataRepository,
) -> None:
    repository.upsert_many("team", [{"id": "football-data:team:57", "name": "A"}])
    repository.upsert_many("team", [{"id": "football-data:team:57", "name": "B"}])

    assert repository.count("team") == 1
    assert repository.list_documents("team") == [
        {"id": "football-data:team:57", "name": "B"}
    ]


def test_upsert_keeps_same_id_in_different_entity_types(
    repository: SQLiteDataRepository,
) -> None:
    document = {"id": "shared-id", "name": "Example"}
    repository.upsert_many("team", [document])
    repository.upsert_many("competition", [document])

    assert repository.count("team") == 1
    assert repository.count("competition") == 1


def test_upsert_rejects_document_without_text_id(
    repository: SQLiteDataRepository,
) -> None:
    with pytest.raises(ValueError, match="text id"):
        repository.upsert_many("team", [{"name": "Missing id"}])
