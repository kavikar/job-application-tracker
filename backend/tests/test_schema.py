"""Constraint tests: prove the schema itself enforces what the
ingestion design leans on, not just that our application code happens
to behave. Once a test triggers an expected constraint violation,
Postgres aborts that transaction -- no further queries in the same
test after that point, which is why each of these is a single
assert-it-fails test rather than continuing on to check more things.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.helpers import insert_application, insert_event


def test_duplicate_raw_email_id_is_rejected(db_session):
    app_id = insert_application(db_session)
    insert_event(db_session, app_id, "application_received", "gmail", raw_email_id="msg-1")

    with pytest.raises(IntegrityError):
        insert_event(db_session, app_id, "interview_invite", "gmail", raw_email_id="msg-1")


def test_multiple_manual_events_with_null_raw_email_id_are_allowed(db_session):
    app_id = insert_application(db_session)
    insert_event(db_session, app_id, "applied", "manual", raw_email_id=None)
    insert_event(db_session, app_id, "interview_invite", "manual", raw_email_id=None)
    # No exception: Postgres does not consider NULLs equal under UNIQUE.

    count = db_session.execute(
        text("SELECT count(*) FROM status_events WHERE application_id = :id"),
        {"id": app_id},
    ).scalar()
    assert count == 2


def test_invalid_status_is_rejected(db_session):
    app_id = insert_application(db_session)
    with pytest.raises(IntegrityError):
        insert_event(db_session, app_id, "not_a_real_status", "manual")


def test_invalid_source_is_rejected(db_session):
    app_id = insert_application(db_session)
    with pytest.raises(IntegrityError):
        insert_event(db_session, app_id, "applied", "carrier_pigeon")


def test_current_status_view_returns_only_latest_event(db_session):
    app_id = insert_application(db_session)
    insert_event(db_session, app_id, "applied", "manual")
    insert_event(db_session, app_id, "application_received", "gmail", raw_email_id="msg-a")
    insert_event(db_session, app_id, "interview_invite", "gmail", raw_email_id="msg-b")

    row = db_session.execute(
        text(
            "SELECT status FROM application_current_status WHERE application_id = :id"
        ),
        {"id": app_id},
    ).fetchone()
    assert row.status == "interview_invite"


def test_current_status_view_excludes_unmatched_events(db_session):
    # An event the entity matcher couldn't resolve (application_id NULL)
    # must not show up as anyone's "current status".
    insert_event(db_session, None, "application_received", "gmail", raw_email_id="msg-unmatched")

    rows = db_session.execute(
        text("SELECT * FROM application_current_status WHERE raw_email_id = 'msg-unmatched'")
    ).fetchall()
    assert rows == []
