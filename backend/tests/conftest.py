import os

# Must happen before anything imports app.config, since Settings()
# reads the environment at construction time.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://jobtracker:jobtracker_dev_pw@localhost:5432/jobtracker_test"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
    """One connection + one transaction per test, rolled back at the
    end. Keeps tests isolated without dropping/recreating the schema
    between every test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
