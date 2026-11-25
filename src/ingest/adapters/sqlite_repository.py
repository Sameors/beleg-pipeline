"""DocumentRepository on SQLite (phase 1). Swap for PostgreSQL later behind the same port."""

import sqlite3
from pathlib import Path

from ingest.domain.models import Document, IngestionEvent, Status

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


class SqliteRepository:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            self.conn.executescript(sql_file.read_text(encoding="utf-8"))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # TODO: implement the methods of ports.repository.DocumentRepository.
    # Tips:
    #   - Always use parameters (?), never f-strings in SQL.
    #   - add_document: `with self.conn:` gives you one transaction for both inserts.
    #   - Catch sqlite3.IntegrityError on the sha256 UNIQUE constraint and raise
    #     DuplicateDocumentError instead (the core must not know about sqlite3).
    #   - Store datetimes as ISO strings, details as json.dumps(dict).

    def ensure_source(self, source_id: str, channel: str, address: str) -> None:
        raise NotImplementedError

    def find_by_sha256(self, sha256: str) -> Document | None:
        raise NotImplementedError

    def get(self, doc_id: str) -> Document | None:
        raise NotImplementedError

    def list_by_status(self, status: Status) -> list[Document]:
        raise NotImplementedError

    def add_document(self, document: Document, event: IngestionEvent) -> None:
        raise NotImplementedError

    def add_event(self, event: IngestionEvent) -> None:
        raise NotImplementedError

    def events_for(self, doc_id: str) -> list[IngestionEvent]:
        raise NotImplementedError

    def count_events(self, event_type: str) -> int:
        raise NotImplementedError
