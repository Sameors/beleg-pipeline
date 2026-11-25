from ingest.domain.models import ErrorCode
from ingest.domain.rules import (
    Decision,
    blob_relative_path,
    decide_by_size,
    decide_by_type,
    make_doc_id,
)

SHA = "abcdef0123456789" * 4


def test_accepted_types() -> None:
    for mime in ["application/pdf", "image/jpeg", "image/png", "image/tiff"]:
        assert decide_by_type(mime) == (Decision.ACCEPT, None)


def test_heic_is_converted() -> None:
    assert decide_by_type("image/heic") == (Decision.CONVERT, None)


def test_unknown_type_is_rejected() -> None:
    assert decide_by_type("application/zip") == (Decision.REJECT, ErrorCode.UNSUPPORTED_TYPE)
    assert decide_by_type(None) == (Decision.REJECT, ErrorCode.UNSUPPORTED_TYPE)


def test_size_limit() -> None:
    assert decide_by_size(100, 1000) == (Decision.ACCEPT, None)
    assert decide_by_size(1001, 1000) == (Decision.QUARANTINE, ErrorCode.TOO_LARGE)


def test_doc_id_is_stable() -> None:
    assert make_doc_id(SHA) == "doc_abcdef012345"
    assert make_doc_id(SHA) == make_doc_id(SHA)


def test_blob_path_is_content_addressed() -> None:
    assert blob_relative_path(SHA, "application/pdf") == f"ab/cd/{SHA}.pdf"
    assert blob_relative_path(SHA, "application/x-unknown").endswith(".bin")
