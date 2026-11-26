import os
import stat
from pathlib import Path

from ingest.adapters.local_blob_store import LocalBlobStore


def test_put_stores_bytes_at_path(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    store.put("ab/cd/abcd.pdf", b"hello")
    assert store.read("ab/cd/abcd.pdf") == b"hello"


def test_put_is_idempotent(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    first = store.put("ab/cd/abcd.pdf", b"hello")
    second = store.put("ab/cd/abcd.pdf", b"hello")
    assert first == second


def test_stored_file_is_read_only(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    path = Path(store.put("ab/cd/abcd.pdf", b"hello"))
    assert not os.access(path, os.W_OK) or not (path.stat().st_mode & stat.S_IWUSR)


def test_no_temp_files_left_behind(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path)
    store.put("ab/cd/abcd.pdf", b"hello")
    assert list(store.iter_paths()) == ["ab/cd/abcd.pdf"]
