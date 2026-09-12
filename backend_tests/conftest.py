from __future__ import annotations

import psycopg
import pytest

from backend.app.config import get_settings
from backend.scripts import migrate


@pytest.fixture
def database_url() -> str:
    return get_settings().database_url


@pytest.fixture
def postgres_ready(database_url: str) -> str:
    try:
        with psycopg.connect(database_url, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres is not available for integration tests: {exc}")

    migrate.main()
    return database_url
