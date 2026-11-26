"""DocumentRepository on SQLite (phase 1). Swap for PostgreSQL later behind the same port."""

import sqlite3
import json
from pathlib import Path

from ingest.domain.models import Document, IngestionEvent, Status
from ingest.ports.repository import DuplicateDocumentError
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
        with self.conn:
            self.conn.execute(
            "INSERT OR IGNORE INTO source (source_id, channel, address) VALUES (?, ?, ?)",
            (source_id, channel, address),
        )

    def find_by_sha256(self, sha256: str) -> Document | None:
        cur = self.conn.execute(
            "SELECT * FROM document WHERE sha256 = ?",
            (sha256,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_document(row)

    def get(self, doc_id: str) -> Document | None:
        cur = self.conn.execute(
            "SELECT * FROM document WHERE doc_id = ?",
            (doc_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_document(row)

    def list_by_status(self, status: Status) -> list[Document]:
        cur = self.conn.execute(
            "SELECT * FROM document WHERE status = ?",
            (status.value,),
        )
        rows = cur.fetchall()
        return [self._row_to_document(row) for row in rows]

    def add_document(self, document: Document, event: IngestionEvent) -> None:
        try:
            with self.conn:
                self.conn.execute(
                    '''INSERT INTO document (doc_id, sha256, original_filename, 
                    source_id, received_at, mime_type, size_bytes, page_count, stored_path, 
                    status, error_code, error_detail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (document.doc_id, document.sha256, document.original_filename, 
                        document.source_id, document.received_at, document.mime_type, 
                        document.size_bytes, document.page_count, document.stored_path, 
                        document.status, document.error_code, document.error_detail),
                )
                self._insert_event(event)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: document.sha256" in str(e):
                raise DuplicateDocumentError from e
            raise
    
    def _insert_event(self, event: IngestionEvent) -> None:
        self.conn.execute(
            '''INSERT INTO ingestion_event (doc_id, event_type, occurred_at, actor, details) 
            VALUES (?, ?, ?, ?, ?)''',
            (event.doc_id, event.event_type.value, event.occurred_at.isoformat(), event.actor, json.dumps(event.details),)
        )
    
        
    def add_event(self, event: IngestionEvent) -> None:
        with self.conn:
            self._insert_event(event)

    def events_for(self, doc_id: str) -> list[IngestionEvent]:
        cur = self.conn.execute(
            "SELECT * FROM ingestion_event WHERE doc_id = ? ORDER BY event_id",
            (doc_id,),
        )
        rows = cur.fetchall()
        return [IngestionEvent(
            doc_id=row["doc_id"],
            event_type=row["event_type"],
            occurred_at=row["occurred_at"],
            actor=row["actor"],
            details=json.loads(row["details"])
        ) for row in rows]

    def count_events(self, event_type: str) -> int:
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM ingestion_event WHERE event_type = ?",
            (event_type,),
        )
        row = cur.fetchone()[0]
        return row

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        return Document(
            doc_id=row["doc_id"],
            sha256=row["sha256"],
            original_filename=row["original_filename"],
            source_id=row["source_id"],
            received_at=row["received_at"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            page_count=row["page_count"],
            stored_path=row["stored_path"],
            status=Status(row["status"]),
            error_code=row["error_code"],
            error_detail=row["error_detail"],
        )