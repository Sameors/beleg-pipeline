"""Business rules for ingestion. Pure functions, fully unit-tested.

See docs/architecture.md, business rules BR-01 to BR-07.
"""

from enum import StrEnum

from ingest.domain.models import ErrorCode

ACCEPTED_MIME_TYPES: frozenset[str] = frozenset(
    {"application/pdf", "image/jpeg", "image/png", "image/tiff"}
)
CONVERTIBLE_MIME_TYPES: frozenset[str] = frozenset({"image/heic", "image/heif"})

EXTENSIONS: dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/tiff": "tif",
    "image/heic": "heic",
    "image/heif": "heif",
}


class Decision(StrEnum):
    ACCEPT = "accept"
    CONVERT = "convert"
    REJECT = "reject"
    QUARANTINE = "quarantine"


def decide_by_size(size_bytes: int, max_size_bytes: int) -> tuple[Decision, ErrorCode | None]:
    """Oversized files are kept (quarantined), not thrown away: they may be real documents."""
    if size_bytes > max_size_bytes:
        return Decision.QUARANTINE, ErrorCode.TOO_LARGE
    return Decision.ACCEPT, None


def decide_by_type(mime_type: str | None) -> tuple[Decision, ErrorCode | None]:
    """BR-04: unsupported formats are rejected with a reason."""
    if mime_type in ACCEPTED_MIME_TYPES:
        return Decision.ACCEPT, None
    if mime_type in CONVERTIBLE_MIME_TYPES:
        return Decision.CONVERT, None
    return Decision.REJECT, ErrorCode.UNSUPPORTED_TYPE


def make_doc_id(sha256: str) -> str:
    """BR-01: one stable ID per unique file, derived from its content."""
    return f"doc_{sha256[:12]}"


def blob_relative_path(sha256: str, mime_type: str) -> str:
    """ADR-01: content-addressed storage, fanned out to keep folders small."""
    ext = EXTENSIONS.get(mime_type, "bin")
    return f"{sha256[:2]}/{sha256[2:4]}/{sha256}.{ext}"
