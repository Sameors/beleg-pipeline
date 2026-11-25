"""Port for storing original files. Phase 1: local folder. Later: Azure Blob Storage."""

from collections.abc import Iterator
from typing import Protocol


class BlobStore(Protocol):
    def put(self, relative_path: str, data: bytes) -> str:
        """Write once, atomically, read-only. Return the stored path.

        Must be idempotent: putting the same path twice is not an error.
        """
        ...

    def exists(self, relative_path: str) -> bool: ...

    def read(self, relative_path: str) -> bytes: ...

    def iter_paths(self) -> Iterator[str]:
        """All stored relative paths. Used by the orphan sweep and integrity check."""
        ...
