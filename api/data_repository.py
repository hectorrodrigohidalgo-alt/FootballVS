import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol


class DataRepository(Protocol):
    """Contrato mínimo que podrán implementar SQLite y Cosmos DB."""

    def upsert_many(self, entity_type: str, documents: Iterable[dict[str, Any]]) -> int:
        """Crea o reemplaza documentos y devuelve la cantidad procesada."""
        ...


class SQLiteDataRepository:
    """Almacén documental local respaldado por SQLite."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        """Crea la carpeta y tabla local si todavía no existen."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    entity_type TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (entity_type, id)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert_many(
        self, entity_type: str, documents: Iterable[dict[str, Any]]
    ) -> int:
        """Inserta o reemplaza por ID; repetir el lote no crea duplicados."""
        serialized_documents: list[tuple[str, str, str]] = []
        for document in documents:
            document_id = document.get("id")
            if not isinstance(document_id, str) or not document_id:
                raise ValueError("Every persisted document requires a text id.")
            serialized_documents.append(
                (
                    entity_type,
                    document_id,
                    json.dumps(document, ensure_ascii=False, sort_keys=True),
                )
            )

        if not serialized_documents:
            return 0

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO documents (entity_type, id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(entity_type, id)
                DO UPDATE SET payload = excluded.payload
                """,
                serialized_documents,
            )
        return len(serialized_documents)

    def list_documents(self, entity_type: str) -> list[dict[str, Any]]:
        """Recupera una colección local en orden estable para API y pruebas."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM documents
                WHERE entity_type = ?
                ORDER BY id
                """,
                (entity_type,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def count(self, entity_type: str) -> int:
        """Cuenta documentos sin cargar sus contenidos."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM documents WHERE entity_type = ?",
                (entity_type,),
            ).fetchone()
        return int(row["total"])
