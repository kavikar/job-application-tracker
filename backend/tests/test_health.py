from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_fails_loudly_if_db_dependency_breaks(client):
    # Prove the endpoint isn't just returning a hardcoded 200 -- if the
    # DB round-trip it depends on can't run, the request should surface
    # a server error, not silently report healthy.
    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        yield  # pragma: no cover -- generator shape required by Depends

    # raise_server_exceptions=False so we get a 500 response back
    # instead of the exception propagating into the test itself.
    app.dependency_overrides[get_db] = broken_db
    response = TestClient(app, raise_server_exceptions=False).get("/health")

    assert response.status_code == 500
    # The client fixture's own teardown clears dependency_overrides
    # after this test, so no manual restore is needed here.
