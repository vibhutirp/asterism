from __future__ import annotations

import psycopg

from backend.scripts import migrate
from backend.scripts import seed_demo as seed_demo_script


def test_migration_creates_expected_tables_and_is_idempotent(postgres_ready: str) -> None:
    migrate.main()
    migrate.main()

    expected_tables = {
        "schema_migrations",
        "workspaces",
        "conversations",
        "messages",
        "galaxies",
        "topics",
        "memories",
    }
    with psycopg.connect(postgres_ready) as conn:
        rows = conn.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            """
        ).fetchall()
        applied = conn.execute("SELECT version FROM schema_migrations").fetchall()

    assert expected_tables <= {row[0] for row in rows}
    assert ("001_create_memory_schema.sql",) in applied


def test_seed_demo_script_can_be_rerun(capsys, postgres_ready: str) -> None:
    seed_demo_script.main()
    first_output = capsys.readouterr().out
    seed_demo_script.main()
    second_output = capsys.readouterr().out

    assert "Seeded" in first_output
    assert "memories across" in first_output
    assert "Seeded" in second_output
    assert "memories across" in second_output
