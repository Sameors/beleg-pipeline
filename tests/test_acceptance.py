"""Acceptance tests for the ingestion stage.

These define "done" (docs/architecture.md, "Acceptance tests"). They fail until the
service and adapters are implemented. Make them green one by one.
"""

import hashlib
import shutil
from pathlib import Path

import pytest

from ingest.cli import FOLDER_SOURCE_ID, App
from ingest.domain.models import ErrorCode, EventType, Status

pytestmark = pytest.mark.acceptance


def ingest(app: App, path: Path):  # type: ignore[no-untyped-def]
    return app.service.ingest_file(path, FOLDER_SOURCE_ID)


def test_01_valid_files_become_received_documents(app: App, fixtures: Path) -> None:
    results = app.service.ingest_folder(fixtures / "valid", FOLDER_SOURCE_ID)
    assert len(results) == 12
    assert all(r.status == Status.RECEIVED for r in results)
    assert len(app.repository.list_by_status(Status.RECEIVED)) == 12


def test_02_same_file_twice_gives_one_document(app: App, fixtures: Path) -> None:
    first = ingest(app, fixtures / "valid" / "invoice_01.pdf")
    second = ingest(app, fixtures / "edge" / "invoice_01_again.pdf")
    assert second.is_duplicate
    assert second.doc_id == first.doc_id
    assert app.repository.count_events(EventType.DUPLICATE_DETECTED) == 1
    assert len(app.repository.list_by_status(Status.RECEIVED)) == 1


def test_03_renamed_jpg_is_detected_by_content(app: App, fixtures: Path) -> None:
    result = ingest(app, fixtures / "edge" / "really_a_jpg.pdf")
    assert result.status == Status.RECEIVED
    doc = app.repository.get(result.doc_id)  # type: ignore[arg-type]
    assert doc is not None and doc.mime_type == "image/jpeg"


def test_04_encrypted_pdf_is_quarantined(app: App, fixtures: Path) -> None:
    result = ingest(app, fixtures / "edge" / "encrypted.pdf")
    assert result.status == Status.QUARANTINED
    assert result.error_code == ErrorCode.ENCRYPTED


def test_05_truncated_pdf_is_quarantined(app: App, fixtures: Path) -> None:
    result = ingest(app, fixtures / "edge" / "truncated.pdf")
    assert result.status == Status.QUARANTINED
    assert result.error_code == ErrorCode.CORRUPT


@pytest.mark.parametrize("name", ["archive.zip", "setup.exe"])
def test_06_zip_and_exe_are_rejected(app: App, fixtures: Path, name: str) -> None:
    result = ingest(app, fixtures / "edge" / name)
    assert result.status == Status.REJECTED
    assert result.error_code == ErrorCode.UNSUPPORTED_TYPE
    assert app.repository.count_events(EventType.DOCUMENT_REJECTED) == 1


def test_07_oversized_file_is_quarantined(app: App, fixtures: Path) -> None:
    result = ingest(app, fixtures / "edge" / "huge_scan.pdf")
    assert result.status == Status.QUARANTINED
    assert result.error_code == ErrorCode.TOO_LARGE


def test_08_heic_is_converted_and_original_kept(app: App, fixtures: Path) -> None:
    heic = fixtures / "edge" / "iphone_photo.heic"
    if not heic.exists():
        pytest.skip("HEIC encoder not available on this platform")
    result = ingest(app, heic)
    assert result.status == Status.RECEIVED
    doc = app.repository.get(result.doc_id)  # type: ignore[arg-type]
    assert doc is not None and doc.stored_path is not None
    # The stored original is byte-identical to the input (BR-02)
    assert app.service.blob_store.read(doc.stored_path) == heic.read_bytes()


def test_09_second_run_adds_nothing(app: App, fixtures: Path) -> None:
    app.service.ingest_folder(fixtures / "valid", FOLDER_SOURCE_ID)
    app.service.ingest_folder(fixtures / "valid", FOLDER_SOURCE_ID)
    assert len(app.repository.list_by_status(Status.RECEIVED)) == 12
    assert app.repository.count_events(EventType.DOCUMENT_RECEIVED) == 12


def test_10_orphan_blob_is_recovered_after_crash(app: App, fixtures: Path) -> None:
    # Simulate a crash between step 6 (blob written) and step 7 (DB insert)
    data = (fixtures / "valid" / "invoice_02.pdf").read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    app.service.blob_store.put(f"{sha[:2]}/{sha[2:4]}/{sha}.pdf", data)

    assert app.service.sweep_orphans() == 1
    assert app.repository.find_by_sha256(sha) is not None
    assert app.service.sweep_orphans() == 0  # idempotent


def test_11_every_blob_rehashes_to_its_sha256(app: App, fixtures: Path, tmp_path: Path) -> None:
    folder = tmp_path / "in"
    shutil.copytree(fixtures / "valid", folder)
    app.service.ingest_folder(folder, FOLDER_SOURCE_ID)
    assert app.service.verify_integrity() == []
