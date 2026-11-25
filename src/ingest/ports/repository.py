"""Port for document metadata and the audit trail. Phase 1: SQLite. Later: PostgreSQL."""

from typing import Protocol

from ingest.domain.models import Document, IngestionEvent, Status


class DocumentRepository(Protocol):
    def ensure_source(self, source_id: str, channel: str, address: str) -> None: ...

    def find_by_sha256(self, sha256: str) -> Document | None: ...

    def get(self, doc_id: str) -> Document | None: ...

    def list_by_status(self, status: Status) -> list[Document]: ...

    def add_document(self, document: Document, event: IngestionEvent) -> None:
        """Insert document and its first event in ONE transaction.

        Raises DuplicateDocumentError if the sha256 already exists
        (two adapters delivering the same file at the same time).
        """
        ...

    def add_event(self, event: IngestionEvent) -> None: ...

    def events_for(self, doc_id: str) -> list[IngestionEvent]: ...

    def count_events(self, event_type: str) -> int: ...


class DuplicateDocumentError(Exception):
    """Raised when a document with the same sha256 is inserted twice."""
