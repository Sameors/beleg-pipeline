"""Folder channel: watches the inbox and hands files to the IngestionService."""

from pathlib import Path

from ingest.service.ingestion import IngestionService


class FolderWatcher:
    def __init__(
        self,
        service: IngestionService,
        inbox: Path,
        processed: Path,
        source_id: str,
        settle_seconds: float,
    ) -> None:
        self.service = service
        self.inbox = inbox
        self.processed = processed
        self.source_id = source_id
        self.settle_seconds = settle_seconds

    def run_once(self) -> None:
        """Process everything currently in the inbox, then return.

        TODO:
          - for each file: result = service.ingest_file(path, source_id)
          - move it to processed/ when status is received, rejected or quarantined
          - leave it in the inbox if an unexpected exception occurs (retry next run)
        """
        raise NotImplementedError

    def watch(self) -> None:
        """Keep running and process new files as they arrive.

        TODO: use watchdog.observers.Observer + FileSystemEventHandler.
        Wait until the file size is stable for settle_seconds before ingesting:
        a file that is still being copied must not be hashed.
        """
        raise NotImplementedError
