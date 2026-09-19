from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from tests.helpers import insert_application, insert_event


def test_create_application_returns_201_with_applied_status(client):
    response = client.post(
        "/applications",
        json={"company": "Acme", "role": "SDET", "job_url": "https://acme.example/jobs/1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["company"] == "Acme"
    assert body["role"] == "SDET"
    assert body["current_status"] == "applied"
    assert "id" in body and "created_at" in body


def test_create_application_writes_the_applied_event(client, db_session):
    response = client.post("/applications", json={"company": "Acme", "role": "SDET"})
    application_id = response.json()["id"]

    row = db_session.execute(
        text(
            "SELECT status, source FROM status_events WHERE application_id = :id"
        ),
        {"id": application_id},
    ).fetchone()
    assert row.status == "applied"
    assert row.source == "manual"


def test_create_application_missing_required_field_is_rejected(client, db_session):
    response = client.post("/applications", json={"company": "Acme"})  # no role
    assert response.status_code == 422

    # Validation must happen before any DB write -- a 422 that still
    # left a half-created row behind would be a worse bug than the
    # validation error itself.
    count = db_session.execute(
        text("SELECT count(*) FROM applications WHERE company = 'Acme'")
    ).scalar()
    assert count == 0


def test_create_application_rejects_empty_company(client):
    response = client.post("/applications", json={"company": "", "role": "SDET"})
    assert response.status_code == 422


def test_list_applications_empty(client):
    response = client.get("/applications")
    assert response.status_code == 200
    assert response.json() == []


def test_create_application_with_applied_at_backdates_both_rows(client, db_session):
    response = client.post(
        "/applications",
        json={"company": "Acme", "role": "SDET", "applied_at": "2026-09-01T00:00:00Z"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["created_at"].startswith("2026-09-01")

    row = db_session.execute(
        text("SELECT created_at FROM status_events WHERE application_id = :id"),
        {"id": body["id"]},
    ).fetchone()
    assert str(row.created_at).startswith("2026-09-01")


def test_create_application_without_applied_at_defaults_to_now(client):
    response = client.post("/applications", json={"company": "Acme", "role": "SDET"})
    created_at = datetime.fromisoformat(response.json()["created_at"])
    assert datetime.now(UTC) - created_at < timedelta(minutes=1)


def test_list_applications_returns_current_status_per_application(client, db_session):
    app_a = insert_application(db_session, company="Acme", role="SDET")
    insert_event(db_session, app_a, "applied", "manual")
    insert_event(db_session, app_a, "interview_invite", "gmail", raw_email_id="msg-1")

    app_b = insert_application(db_session, company="Globex", role="SRE")
    insert_event(db_session, app_b, "applied", "manual")

    response = client.get("/applications")
    assert response.status_code == 200
    by_company = {row["company"]: row["current_status"] for row in response.json()}
    assert by_company == {"Acme": "interview_invite", "Globex": "applied"}
