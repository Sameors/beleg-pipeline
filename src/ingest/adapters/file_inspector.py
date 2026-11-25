"""FileInspector and Converter using filetype, pikepdf and pillow-heif."""

from ingest.domain.models import ErrorCode


class DefaultFileInspector:
    def detect_mime(self, data: bytes) -> str | None:
        """TODO: kind = filetype.guess(data); return kind.mime if kind else None."""
        raise NotImplementedError

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
        raise NotImplementedError


class HeicConverter:
    def convert(self, data: bytes, mime_type: str) -> tuple[bytes, str]:
        """TODO:
        - pillow_heif.register_heif_opener() once (e.g. in __init__)
        - Image.open(io.BytesIO(data)).convert("RGB").save(buf, "JPEG", quality=90)
        - return buf.getvalue(), "image/jpeg"
        - wrap any exception in ports.file_inspector.ConversionError
        Open question in the architecture doc: JPEG or PDF as target format?
        """
        raise NotImplementedError
