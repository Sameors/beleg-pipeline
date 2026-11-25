"""Configuration, read from environment variables or a .env file (prefix INGEST_)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INGEST_", env_file=".env", extra="ignore")

    inbox_dir: Path = Path("data/inbox")
    processed_dir: Path = Path("data/processed")
    store_dir: Path = Path("data/store")
    db_path: Path = Path("data/ingest.db")

    max_size_mb: int = 50
    max_pages: int = 200
    settle_seconds: float = 2.0  # folder watcher waits until file size is stable

    @property
    def max_size_bytes(self) -> int:
        return self.max_size_mb * 1024 * 1024
