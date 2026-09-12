"""Tiny migration runner.

Not Alembic on purpose: the schema here is two tables and a view,
defined once in Phase 1 and expected to change rarely. Alembic's
ORM-model-diffing machinery solves a problem (autogenerating migrations
from model drift) this project doesn't have. This is the same pattern
Flyway/golang-migrate use: numbered plain-SQL files, a table tracking
which ones already ran, apply whatever's new. If schema churn picks up
later, this is the first thing worth swapping for something heavier.
"""

from pathlib import Path

from sqlalchemy import Engine, create_engine, text

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def applied_migrations(engine: Engine) -> set[str]:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        rows = conn.execute(text("SELECT id FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def pending_migrations(engine: Engine) -> list[Path]:
    already_applied = applied_migrations(engine)
    all_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [m for m in all_migrations if m.name not in already_applied]


def run_migrations(engine: Engine) -> list[str]:
    """Apply pending migrations in order. Returns names of migrations applied."""
    applied_now = []
    for migration_path in pending_migrations(engine):
        sql = migration_path.read_text()
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (id) VALUES (:id)"),
                {"id": migration_path.name},
            )
        applied_now.append(migration_path.name)
    return applied_now


if __name__ == "__main__":
    from app.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url)
    applied_now = run_migrations(engine)
    if applied_now:
        print(f"Applied {len(applied_now)} migration(s): {', '.join(applied_now)}")
    else:
        print("No pending migrations.")
