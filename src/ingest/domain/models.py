"""Domain models for the ingestion stage."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    RECEIVED = "received"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    DELETED = "deleted"


class EventType(StrEnum):
    DOCUMENT_RECEIVED = "DocumentReceived"
    DUPLICATE_DETECTED = "DuplicateDetected"
    DOCUMENT_REJECTED = "DocumentRejected"
    DOCUMENT_QUARANTINED = "DocumentQuarantined"
    DOCUMENT_DELETED = "DocumentDeleted"
    ORPHAN_RECOVERED = "OrphanRecovered"


class ErrorCode(StrEnum):
    UNSUPPORTED_TYPE = "unsupported_type"
    TOO_LARGE = "too_large"
    TOO_MANY_PAGES = "too_many_pages"
    ENCRYPTED = "encrypted"
    CORRUPT = "corrupt"
    CONVERSION_FAILED = "conversion_failed"


class Channel(StrEnum):
    FOLDER = "folder"
    EMAIL = "email"
    UPLOAD = "upload"


class Document(BaseModel):
    doc_id: str
    sha256: str
    original_filename: str
    source_id: str
    received_at: datetime
    mime_type: str
    size_bytes: int
    page_count: int | None = None
    stored_path: str | None = None
    status: Status
    error_code: ErrorCode | None = None
    error_detail: str | None = None


class IngestionEvent(BaseModel):
    doc_id: str | None  # None for rejected files: they never become a Document
    event_type: EventType
    occurred_at: datetime
    actor: str
    details: dict[str, str] = {}


class IngestResult(BaseModel):
    """What the service returns to the channel adapter."""

    doc_id: str | None
    status: Status
    is_duplicate: bool = False
    error_code: ErrorCode | None = None
