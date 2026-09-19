from sqlalchemy import text

from tests.helpers import insert_application, insert_event


def test_get_application_events_returns_chronological_timeline(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, app_id, "applied", "manual")
    insert_event(db_session, app_id, "application_received", "gmail", raw_email_id="msg-1")
    insert_event(db_session, app_id, "interview_invite", "gmail", raw_email_id="msg-2")

    response = client.get(f"/applications/{app_id}/events")
    assert response.status_code == 200
    statuses = [row["status"] for row in response.json()]
    assert statuses == ["applied", "application_received", "interview_invite"]


def test_get_application_events_empty_for_application_with_no_events(client, db_session):
    # id that doesn't correspond to any row -- endpoint should just
    # return an empty list, not error, since it's a query not a lookup.
    response = client.get("/applications/999999/events")
    assert response.status_code == 200
    assert response.json() == []


def test_get_unmatched_events_excludes_linked_events(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, app_id, "applied", "manual")  # linked, must not show up
    insert_event(db_session, None, "interview_invite", "gmail", raw_email_id="msg-unmatched")

    response = client.get("/events/unmatched")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["raw_email_id"] == "msg-unmatched"


def test_link_event_sets_application_id(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, None, "interview_invite", "gmail", raw_email_id="msg-unmatched")
    event_id = db_session.execute(
        text("SELECT id FROM status_events WHERE raw_email_id = 'msg-unmatched'")
    ).scalar()

    response = client.patch(f"/events/{event_id}/link", json={"application_id": app_id})
    assert response.status_code == 200
    assert response.json()["id"] == event_id

    # No longer shows up as unmatched.
    unmatched = client.get("/events/unmatched").json()
    assert unmatched == []


def test_link_event_that_is_already_linked_returns_404(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, app_id, "applied", "manual")
    event_id = db_session.execute(
        text("SELECT id FROM status_events WHERE application_id = :id"),
        {"id": app_id},
    ).scalar()

    response = client.patch(f"/events/{event_id}/link", json={"application_id": app_id})
    assert response.status_code == 404


def test_link_event_to_nonexistent_application_returns_404(client, db_session):
    insert_event(db_session, None, "interview_invite", "gmail", raw_email_id="msg-x")
    event_id = db_session.execute(
        text("SELECT id FROM status_events WHERE raw_email_id = 'msg-x'")
    ).scalar()

    response = client.patch(f"/events/{event_id}/link", json={"application_id": 999999})
    assert response.status_code == 404


def test_add_status_event_updates_current_status(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, app_id, "applied", "manual")

    response = client.post(f"/applications/{app_id}/events", json={"status": "rejected"})
    assert response.status_code == 201
    assert response.json()["status"] == "rejected"
    assert response.json()["source"] == "manual"

    current = client.get("/applications").json()
    assert current[0]["current_status"] == "rejected"


def test_add_status_event_with_occurred_at_backdates_it(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    insert_event(db_session, app_id, "applied", "manual")

    response = client.post(
        f"/applications/{app_id}/events",
        json={"status": "rejected", "occurred_at": "2026-09-17T00:00:00Z"},
    )
    assert response.status_code == 201
    assert response.json()["created_at"].startswith("2026-09-17")


def test_add_status_event_to_nonexistent_application_returns_404(client):
    response = client.post("/applications/999999/events", json={"status": "rejected"})
    assert response.status_code == 404


def test_add_status_event_rejects_invalid_status(client, db_session):
    app_id = insert_application(db_session, company="Acme")
    response = client.post(
        f"/applications/{app_id}/events", json={"status": "not_a_real_status"}
    )
    assert response.status_code == 422
