"""IngestionService: the core of the ingestion stage.

This module only knows the ports (interfaces), never a concrete adapter.
It is the ONLY code allowed to write to the blob store and the repository.

Status: skeleton. Each step below is yours to implement. The acceptance tests in
tests/test_acceptance.py define when it is done.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from ingest.config import Settings
from ingest.domain.models import IngestResult
from ingest.ports.blob_store import BlobStore
from ingest.ports.file_inspector import Converter, FileInspector
from ingest.ports.repository import DocumentRepository


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        blob_store: BlobStore,
        repository: DocumentRepository,
        inspector: FileInspector,
        converter: Converter,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        actor: str = "ingestion-service",
    ) -> None:
        self.settings = settings
        self.blob_store = blob_store
        self.repository = repository
        self.inspector = inspector
        self.converter = converter
        self.clock = clock
        self.actor = actor

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def ingest_file(self, path: Path, source_id: str) -> IngestResult:
        """Ingest one file. Same file twice -> same doc_id (idempotent).

        Sequence (docs/architecture.md, "Processing sequence"):
          1. Read bytes; check size        -> quarantine if too large   (rules.decide_by_size)
          2. Compute SHA-256               -> known? log DuplicateDetected, return existing doc_id
          3. Detect type from magic bytes  -> unsupported? log DocumentRejected, return
          4. Check readability (PDFs)      -> encrypted/corrupt? store original, quarantine
          5. Convert if needed (HEIC)      -> failure? quarantine with CONVERSION_FAILED
          6. Store the ORIGINAL bytes      -> blob_store.put (atomic, read-only)
          7. Register Document + event     -> repository.add_document (one transaction)
          8. Return IngestResult
        """
        # TODO(step 1-8): implement. Suggested shape:
        #   data = path.read_bytes()
        #   if (result := self._check_size(...)): return result
        #   sha = hashlib.sha256(data).hexdigest()
        #   if (result := self._check_duplicate(...)): return result
        #   ...
        raise NotImplementedError("ingest_file: implement steps 1-8")

    def ingest_folder(self, folder: Path, source_id: str) -> list[IngestResult]:
        """Ingest every file in a folder (non-recursive), sorted by name for repeatable runs."""
        # TODO: loop over files, call ingest_file, collect results.
        #       Moving handled files to processed/ is the folder adapter's job, not this one.
        raise NotImplementedError("ingest_folder")

    def sweep_orphans(self) -> int:
        """After a crash: register blobs that have no Document row. Return how many.

        NFR-01. Hint: iterate blob_store.iter_paths(); the file name is the sha256.
        """
        raise NotImplementedError("sweep_orphans")

    def verify_integrity(self) -> list[str]:
        """Re-hash every stored blob. Return doc_ids whose hash no longer matches. NFR-03."""
        raise NotImplementedError("verify_integrity")

    # ------------------------------------------------------------------ #
    # Helpers you will probably want
    # ------------------------------------------------------------------ #
    def _now(self) -> datetime:
        return self.clock()
