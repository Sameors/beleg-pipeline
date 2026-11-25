"""Command-line entry point: `ingest <command>`.

This is the composition root: the only place where concrete adapters are wired
into the service. Swapping SQLite for PostgreSQL later means changing build_service only.
"""

from dataclasses import dataclass

import typer

from ingest.adapters.file_inspector import DefaultFileInspector, HeicConverter
from ingest.adapters.folder_watcher import FolderWatcher
from ingest.adapters.local_blob_store import LocalBlobStore
from ingest.adapters.sqlite_repository import SqliteRepository
from ingest.config import Settings
from ingest.domain.models import Status
from ingest.service.ingestion import IngestionService

FOLDER_SOURCE_ID = "src_folder_inbox"

app = typer.Typer(help="Ingestion stage of the rental document pipeline.")


@dataclass
class App:
    settings: Settings
    repository: SqliteRepository
    service: IngestionService


def build_app(settings: Settings | None = None) -> App:
    settings = settings or Settings()
    repository = SqliteRepository(settings.db_path)
    service = IngestionService(
        settings=settings,
        blob_store=LocalBlobStore(settings.store_dir),
        repository=repository,
        inspector=DefaultFileInspector(),
        converter=HeicConverter(),
    )
    return App(settings=settings, repository=repository, service=service)


def _watcher(a: App) -> FolderWatcher:
    a.repository.ensure_source(FOLDER_SOURCE_ID, "folder", str(a.settings.inbox_dir))
    return FolderWatcher(
        service=a.service,
        inbox=a.settings.inbox_dir,
        processed=a.settings.processed_dir,
        source_id=FOLDER_SOURCE_ID,
        settle_seconds=a.settings.settle_seconds,
    )


@app.command("run-once")
def run_once() -> None:
    """Process everything in the inbox, then exit."""
    _watcher(build_app()).run_once()


@app.command()
def watch() -> None:
    """Keep running and process new files as they arrive."""
    _watcher(build_app()).watch()


@app.command()
def sweep() -> None:
    """Register blobs left without a database row after a crash."""
    count = build_app().service.sweep_orphans()
    typer.echo(f"Recovered {count} orphan blob(s).")


@app.command()
def verify() -> None:
    """Re-hash every stored blob and report mismatches."""
    bad = build_app().service.verify_integrity()
    typer.echo("All blobs intact." if not bad else f"Mismatch: {', '.join(bad)}")
    raise typer.Exit(code=1 if bad else 0)


@app.command()
def quarantine() -> None:
    """List quarantined documents with their reasons."""
    for doc in build_app().repository.list_by_status(Status.QUARANTINED):
        typer.echo(f"{doc.doc_id}  {doc.error_code}  {doc.original_filename}")


if __name__ == "__main__":
    app()
