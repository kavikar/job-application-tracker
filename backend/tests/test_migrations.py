from sqlalchemy import inspect, text

from db.migrate import run_migrations


def test_migration_creates_expected_tables(test_engine):
    inspector = inspect(test_engine)
    tables = set(inspector.get_table_names())
    assert {
        "applications",
        "status_events",
        "target_companies",
        "schema_migrations",
    } <= tables

    views = set(inspector.get_view_names())
    assert "application_current_status" in views


def test_migration_is_idempotent(test_engine):
    # Already applied once by the test_engine fixture -- running again
    # must apply nothing and must not error.
    applied_again = run_migrations(test_engine)
    assert applied_again == []


def test_status_events_columns(test_engine):
    inspector = inspect(test_engine)
    columns = {col["name"] for col in inspector.get_columns("status_events")}
    assert columns == {
        "id",
        "application_id",
        "status",
        "source",
        "raw_email_id",
        "created_at",
    }


def test_schema_migrations_tracks_applied_file(test_engine):
    with test_engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM schema_migrations")).fetchall()
    assert ("0001_init.sql",) in rows
    assert ("0002_target_companies.sql",) in rows
