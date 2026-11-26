from pathlib import Path

import pytest

from ingest.adapters.file_inspector import DefaultFileInspector, HeicConverter
from ingest.domain.models import ErrorCode
from ingest.ports.file_inspector import ConversionError

inspector = DefaultFileInspector()


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("valid/invoice_01.pdf", "application/pdf"),
        ("valid/receipt_photo.jpg", "image/jpeg"),
        ("valid/meter_reading.png", "image/png"),
        ("edge/really_a_jpg.pdf", "image/jpeg"),  # name says PDF, content says JPEG
        ("edge/archive.zip", "application/zip"),
    ],
)
def test_detect_mime_by_content(fixtures: Path, name: str, expected: str) -> None:
    assert inspector.detect_mime((fixtures / name).read_bytes()) == expected


def test_detect_mime_unknown_bytes() -> None:
    assert inspector.detect_mime(b"just some text") is None


def test_valid_pdf_page_count(fixtures: Path) -> None:
    data = (fixtures / "valid" / "invoice_01.pdf").read_bytes()
    assert inspector.check_pdf(data) == (2, None)


def test_encrypted_pdf(fixtures: Path) -> None:
    data = (fixtures / "edge" / "encrypted.pdf").read_bytes()
    assert inspector.check_pdf(data) == (None, ErrorCode.ENCRYPTED)


def test_truncated_pdf_is_corrupt(fixtures: Path) -> None:
    data = (fixtures / "edge" / "truncated.pdf").read_bytes()
    assert inspector.check_pdf(data) == (None, ErrorCode.CORRUPT)


def test_heic_converts_to_jpeg(fixtures: Path) -> None:
    heic = fixtures / "edge" / "iphone_photo.heic"
    if not heic.exists():
        pytest.skip("HEIC encoder not available on this platform")
    data, mime = HeicConverter().convert(heic.read_bytes(), "image/heic")
    assert mime == "image/jpeg"
    assert data[:2] == b"\xff\xd8"  # every JPEG starts with these two bytes


def test_conversion_failure_raises_conversion_error() -> None:
    with pytest.raises(ConversionError):
        HeicConverter().convert(b"not an image", "image/heic")
