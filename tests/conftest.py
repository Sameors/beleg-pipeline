from collections.abc import Iterator
from pathlib import Path

import pytest

from ingest.cli import FOLDER_SOURCE_ID, App, build_app
from ingest.config import Settings
from tests.fixtures.make_fixtures import make_fixtures


@pytest.fixture(scope="session")
def fixtures(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generated once per test session."""
    return make_fixtures(tmp_path_factory.mktemp("fixtures"))


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Every test gets its own empty store and database."""
    return Settings(
        inbox_dir=tmp_path / "inbox",
        processed_dir=tmp_path / "processed",
        store_dir=tmp_path / "store",
        db_path=tmp_path / "ingest.db",
        settle_seconds=0,
    )


@pytest.fixture
def app(settings: Settings) -> Iterator[App]:
    a = build_app(settings)
    a.repository.ensure_source(FOLDER_SOURCE_ID, "folder", str(settings.inbox_dir))
    yield a
    a.repository.close()
