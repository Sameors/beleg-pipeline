"""FileInspector and Converter using filetype, pikepdf and pillow-heif."""

import io

import pikepdf
import pillow_heif
from filetype import filetype
from PIL import Image

from ingest.domain.models import ErrorCode
from ingest.ports.file_inspector import ConversionError


class DefaultFileInspector:
    def detect_mime(self, data: bytes) -> str | None:
        """Mime type from magic bytes (ADR-0005), never from the file extension."""
        kind = filetype.guess(data)
        return kind.mime if kind else None

    def check_pdf(self, data: bytes) -> tuple[int | None, ErrorCode | None]:
        """TODO:
        - open with pikepdf.open(io.BytesIO(data), attempt_recovery=False)
          TRAP: qpdf silently repairs damaged PDFs by default, so a truncated file
          "opens fine" and loses pages without telling you. Fail instead, and quarantine.
        - pikepdf.PasswordError -> (None, ErrorCode.ENCRYPTED)
        - pikepdf.PdfError      -> (None, ErrorCode.CORRUPT)
        - else                  -> (len(pdf.pages), None)
        Never render the PDF or run anything inside it.
        """

        try:
            with pikepdf.open(io.BytesIO(data), attempt_recovery=False) as pdf:
                return len(pdf.pages), None
        except pikepdf.PasswordError:
            return None, ErrorCode.ENCRYPTED
        except pikepdf.PdfError:
            return None, ErrorCode.CORRUPT


class HeicConverter:
    def convert(self, data: bytes, mime_type: str) -> tuple[bytes, str]:
        """TODO:
        - pillow_heif.register_heif_opener() once (e.g. in __init__)
        - Image.open(io.BytesIO(data)).convert("RGB").save(buf, "JPEG", quality=90)
        - return buf.getvalue(), "image/jpeg"
        - wrap any exception in ports.file_inspector.ConversionError
        Open question in the architecture doc: JPEG or PDF as target format?
        """

        pillow_heif.register_heif_opener()
        try:
            with io.BytesIO(data) as buf, Image.open(buf) as img:
                img = img.convert("RGB")
                out_buf = io.BytesIO()
                img.save(out_buf, "JPEG", quality=90)
                return out_buf.getvalue(), "image/jpeg"
        except Exception as e:
            raise ConversionError from e
