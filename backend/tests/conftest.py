import os

# Must happen before anything imports app.config, since Settings()
# reads the environment at construction time.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://jobtracker:jobtracker_dev_pw@localhost:5432/jobtracker_test"
)
os.environ["API_KEY"] = "test-api-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.main import app
from db.migrate import run_migrations

get_settings.cache_clear()


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(get_settings().database_url)
    run_migrations(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """One connection + one outer transaction per test, rolled back at
    the end -- but app code (e.g. create_application) legitimately
    calls session.commit() as part of a real request. Plain
    Session(bind=connection) would let that commit the outer
    transaction for real, leaking data into the shared test database
    between tests. join_transaction_mode="create_savepoint" makes the
    session's commit()/rollback() operate on a SAVEPOINT instead: app
    code sees normal commit semantics, but nothing is visible outside
    this test until the outer transaction itself is committed -- which
    it never is; it's always rolled back below."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session):
    """Authenticated by default -- almost every existing test exercises
    a now-protected route and isn't testing auth itself, so retrofitting
    an explicit header onto ~50 call sites would just be noise. The
    dedicated auth tests use their own unauthenticated TestClient
    instead of this fixture."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(
            app, headers={"Authorization": f"Bearer {get_settings().api_key}"}
        )
    finally:
        app.dependency_overrides.clear()
