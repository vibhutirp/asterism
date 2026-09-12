from __future__ import annotations

import runpy
import warnings

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


def test_backend_scripts_execute_as_modules(capsys, postgres_ready: str) -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*found in sys.modules.*", category=RuntimeWarning)
        runpy.run_module("backend.scripts.migrate", run_name="__main__")
        runpy.run_module("backend.scripts.seed_demo", run_name="__main__")

    assert "Seeded" in capsys.readouterr().out


def test_migration_applies_new_migration_from_configured_directory(monkeypatch, tmp_path, postgres_ready: str) -> None:
    marker_table = "coverage_marker_migration"
    migration = tmp_path / "999_coverage_marker.sql"
    migration.write_text(f"CREATE TABLE IF NOT EXISTS {marker_table} (id integer PRIMARY KEY);")
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)

    try:
        migrate.main()
        migrate.main()
        with psycopg.connect(postgres_ready) as conn:
            exists = conn.execute("SELECT to_regclass(%s)", (marker_table,)).fetchone()[0]
    finally:
        with psycopg.connect(postgres_ready) as conn:
            conn.execute(f"DROP TABLE IF EXISTS {marker_table}")
            conn.execute("DELETE FROM schema_migrations WHERE version = %s", (migration.name,))

    assert exists == marker_table
