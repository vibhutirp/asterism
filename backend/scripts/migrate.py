from __future__ import annotations

from pathlib import Path

import psycopg

from backend.app.config import get_settings


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def main() -> None:
    settings = get_settings()
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version text PRIMARY KEY,
              applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration.name
            if version in applied:
                continue
            with conn.transaction():
                conn.execute(migration.read_text())
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
            print(f"Applied {version}")


if __name__ == "__main__":
    main()
