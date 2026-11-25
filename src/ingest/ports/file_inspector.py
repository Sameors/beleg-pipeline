"""Port for looking at file bytes: type, PDF structure, conversion."""

from typing import Protocol

from ingest.domain.models import ErrorCode


class FileInspector(Protocol):
    def detect_mime(self, data: bytes) -> str | None:
        """Mime type from magic bytes (ADR-05), never from the file extension."""
        ...

    def check_pdf(self, data: bytes) -> tuple[int | None, ErrorCode | None]:
        """Return (page_count, error). Error is ENCRYPTED or CORRUPT, else None."""
        ...


class Converter(Protocol):
    def convert(self, data: bytes, mime_type: str) -> tuple[bytes, str]:
        """Convert e.g. HEIC to JPEG. Return (new_bytes, new_mime_type).

        Raises ConversionError on failure. The original is still stored as-is.
        """
        ...


class ConversionError(Exception):
    pass
