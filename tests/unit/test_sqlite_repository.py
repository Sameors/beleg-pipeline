from datetime import UTC, datetime
from pathlib import Path

import pytest

from ingest.adapters.sqlite_repository import SqliteRepository
from ingest.domain.models import Document, ErrorCode, EventType, IngestionEvent, Status
from ingest.ports.repository import DuplicateDocumentError

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
SHA = "9f3a" + "0" * 60


def make_doc(sha: str = SHA) -> Document:
    return Document(
        doc_id=f"doc_{sha[:12]}",
        sha256=sha,
        original_filename="Hausgeld.pdf",
        source_id="src_test",
        received_at=NOW,
        mime_type="application/pdf",
        size_bytes=1234,
        page_count=3,
        stored_path=f"9f/3a/{sha}.pdf",
        status=Status.RECEIVED,
    )


def make_event(doc_id: str) -> IngestionEvent:
    return IngestionEvent(
        doc_id=doc_id, event_type=EventType.DOCUMENT_RECEIVED, occurred_at=NOW, actor="test"
    )


@pytest.fixture
def repo(tmp_path: Path):  # type: ignore[no-untyped-def]
    print("\n[fixture] creating db in", tmp_path)
    r = SqliteRepository(tmp_path / "test.db")
    r.ensure_source("src_test", "folder", "/inbox")
    yield r
    r.close()


def test_ensure_source_twice_is_harmless(repo: SqliteRepository) -> None:
    repo.ensure_source("src_test", "folder", "/inbox")


def test_unknown_sha_returns_none(repo: SqliteRepository) -> None:
    assert repo.find_by_sha256("nope") is None


def test_add_and_find_document(repo: SqliteRepository) -> None:
    doc = make_doc()
    repo.add_document(doc, make_event(doc.doc_id))
    found = repo.find_by_sha256(SHA)
    assert found is not None
    assert found.doc_id == doc.doc_id
    assert found.status == Status.RECEIVED
    assert found.page_count == 3


def test_add_document_also_writes_event(repo: SqliteRepository) -> None:
    doc = make_doc()
    repo.add_document(doc, make_event(doc.doc_id))
    assert repo.count_events(EventType.DOCUMENT_RECEIVED) == 1


def test_same_sha_twice_raises_duplicate(repo: SqliteRepository) -> None:
    doc = make_doc()
    repo.add_document(doc, make_event(doc.doc_id))
    with pytest.raises(DuplicateDocumentError):
        repo.add_document(doc, make_event(doc.doc_id))
    assert repo.count_events(EventType.DOCUMENT_RECEIVED) == 1


def test_error_fields_survive_round_trip(repo: SqliteRepository) -> None:
    doc = make_doc().model_copy(
        update={
            "status": Status.QUARANTINED,
            "error_code": ErrorCode.ENCRYPTED,
            "error_detail": "password required",
        }
    )
    repo.add_document(doc, make_event(doc.doc_id))
    found = repo.find_by_sha256(SHA)
    assert found is not None
    assert found.error_code == ErrorCode.ENCRYPTED
    assert found.error_detail == "password required"


def test_get_by_doc_id(repo: SqliteRepository) -> None:
    doc = make_doc()
    repo.add_document(doc, make_event(doc.doc_id))
    assert repo.get(doc.doc_id) is not None
    assert repo.get("doc_missing") is None


def test_list_by_status(repo: SqliteRepository) -> None:
    a = make_doc("aa" + "0" * 62)
    b = make_doc("bb" + "0" * 62).model_copy(update={"status": Status.QUARANTINED})
    repo.add_document(a, make_event(a.doc_id))
    repo.add_document(b, make_event(b.doc_id))
    assert [d.doc_id for d in repo.list_by_status(Status.RECEIVED)] == [a.doc_id]
    assert [d.doc_id for d in repo.list_by_status(Status.QUARANTINED)] == [b.doc_id]


def test_events_for_returns_details(repo: SqliteRepository) -> None:
    doc = make_doc()
    repo.add_document(doc, make_event(doc.doc_id))
    repo.add_event(
        IngestionEvent(
            doc_id=doc.doc_id,
            event_type=EventType.DUPLICATE_DETECTED,
            occurred_at=NOW,
            actor="test",
            details={"filename": "copy.pdf"},
        )
    )
    events = repo.events_for(doc.doc_id)
    # events = repo.events_for(doc.doc_id)
    assert [e.event_type for e in events] == [
        EventType.DOCUMENT_RECEIVED,
        EventType.DUPLICATE_DETECTED,
    ]
    assert events[1].details == {"filename": "copy.pdf"}
