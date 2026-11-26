"""BlobStore on the local file system."""

import os
from collections.abc import Iterator
from pathlib import Path


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, relative_path: str, data: bytes) -> str:
        """Write once, atomically, read-only.

        TODO:

          - target = self.root / relative_path; if it exists, return it (idempotent)
          - write to a temp file in the SAME folder (e.g. target.with_suffix(".tmp"))
          - os.replace(tmp, target)  -> atomic on Windows and Unix
          - target.chmod(0o444)      -> read-only
        Why temp + rename: a crash mid-write must never leave a half file at the final path.
        """

        target = self.root / relative_path
        if target.exists():
            return str(target)

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
        target.chmod(0o444)
        return str(target)

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()

    def read(self, relative_path: str) -> bytes:
        return (self.root / relative_path).read_bytes()

    def iter_paths(self) -> Iterator[str]:
        for p in self.root.rglob("*"):
            if p.is_file() and p.suffix != ".tmp":
                yield p.relative_to(self.root).as_posix()
