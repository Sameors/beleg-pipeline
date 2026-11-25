"""Generate the tricky test files instead of committing binaries (and never real documents).

Run directly:  python tests/fixtures/make_fixtures.py
Tests call make_fixtures(tmp_path) automatically.
"""

import io
import shutil
import sys
import zipfile
from pathlib import Path

import pikepdf
from PIL import Image


def _pdf(title: str, pages: int = 1) -> bytes:
    pdf = pikepdf.new()
    for _ in range(pages):
        pdf.add_blank_page()
    pdf.docinfo["/Title"] = title  # makes each file's hash unique
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def _image(fmt: str, color: tuple[int, int, int]) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 280), color).save(buf, fmt)
    return buf.getvalue()


def make_fixtures(root: Path) -> Path:
    """Create fixtures under root and return root.

    valid/  12 files that must all become documents with status 'received'
    edge/   one file per edge case
    """
    valid, edge = root / "valid", root / "edge"
    valid.mkdir(parents=True, exist_ok=True)
    edge.mkdir(parents=True, exist_ok=True)

    # 10 PDFs + 2 images = 12 valid files
    for i in range(1, 11):
        (valid / f"invoice_{i:02d}.pdf").write_bytes(_pdf(f"Invoice {i}", pages=1 + i % 3))
    (valid / "receipt_photo.jpg").write_bytes(_image("JPEG", (240, 240, 230)))
    (valid / "meter_reading.png").write_bytes(_image("PNG", (230, 240, 250)))

    # Duplicate: identical bytes, different name
    shutil.copy(valid / "invoice_01.pdf", edge / "invoice_01_again.pdf")

    # JPG renamed to .pdf
    (edge / "really_a_jpg.pdf").write_bytes(_image("JPEG", (200, 220, 210)))

    # Password-protected PDF
    pdf = pikepdf.new()
    pdf.add_blank_page()
    buf = io.BytesIO()
    pdf.save(buf, encryption=pikepdf.Encryption(owner="owner", user="secret"))
    (edge / "encrypted.pdf").write_bytes(buf.getvalue())

    # Truncated PDF: header intact, body cut off
    full = _pdf("Truncated", pages=3)
    (edge / "truncated.pdf").write_bytes(full[: len(full) // 3])

    # ZIP and EXE: must be rejected
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        z.writestr("readme.txt", "not a document")
    (edge / "archive.zip").write_bytes(zbuf.getvalue())
    (edge / "setup.exe").write_bytes(b"MZ" + b"\x90\x00" * 64 + b"PE\x00\x00" + b"\x00" * 512)

    # 60 MB file: must be quarantined as too large
    with open(edge / "huge_scan.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n")
        f.truncate(60 * 1024 * 1024)

    # iPhone photo (HEIC)
    try:
        import pillow_heif

        heif = pillow_heif.from_pillow(Image.new("RGB", (200, 280), (250, 230, 220)))
        hbuf = io.BytesIO()
        heif.save(hbuf, format="HEIF", quality=80)
        (edge / "iphone_photo.heic").write_bytes(hbuf.getvalue())
    except Exception as exc:  # encoder missing on some platforms
        print(f"warning: could not create HEIC fixture: {exc}", file=sys.stderr)

    return root


if __name__ == "__main__":
    out = make_fixtures(Path(__file__).parent / "generated")
    print(f"Fixtures written to {out}")
