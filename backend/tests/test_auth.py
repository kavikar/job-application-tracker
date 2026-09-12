from fastapi.testclient import TestClient

from app.main import app


def test_health_requires_no_api_key():
    # Deliberately public -- see the comment on the /health route.
    response = TestClient(app).get("/health")
    assert response.status_code == 200


def test_protected_route_without_api_key_is_rejected():
    response = TestClient(app).get("/applications")
    assert response.status_code == 401


def test_protected_route_with_wrong_api_key_is_rejected():
    response = TestClient(app, headers={"Authorization": "Bearer wrong-key"}).get(
        "/applications"
    )
    assert response.status_code == 401


def test_protected_route_with_correct_api_key_succeeds(client):
    # `client` fixture already sends the correct key by default.
    response = client.get("/applications")
    assert response.status_code == 200


def test_ingest_is_protected_too():
    response = TestClient(app).post("/ingest")
    assert response.status_code == 401


def test_link_event_is_protected_too():
    response = TestClient(app).patch("/events/1/link", json={"application_id": 1})
    assert response.status_code == 401
