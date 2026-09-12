# Backend

FastAPI + Postgres. See `/DESIGN.md` at the repo root for the overall
design and tradeoffs.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Postgres running locally, with a role/db matching .env.example
cp .env.example .env

# Apply migrations (must run as a module, from the backend/ dir, so
# the app package resolves the same way pytest's pythonpath=. does)
.venv/bin/python -m db.migrate

.venv/bin/uvicorn app.main:app --reload
```

## Tests

```bash
.venv/bin/python -m pytest -v
```

Tests run against a real local Postgres database (`jobtracker_test`),
not a mock — see `tests/conftest.py` and `DESIGN.md` for why. Each
test runs inside a transaction that's rolled back afterward, so the
schema only needs to be migrated once per test session.

## Schema

Numbered plain-SQL files in `db/migrations/`, applied by
`db/migrate.py`, which tracks what's already run in a
`schema_migrations` table. Not Alembic — see the comment at the top of
`db/migrate.py` for why that's the right call at this size.
