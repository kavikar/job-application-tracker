from sqlalchemy import text

from app.gmail_client import RawEmail
from app.ingestion import run_ingestion
from tests.fakes import FakeGmailClient
from tests.helpers import insert_application


def test_classified_and_matched_email_creates_linked_status_event(db_session):
    app_id = insert_application(db_session, company="Acme", role="SDET")
    gmail = FakeGmailClient(
        [
            RawEmail(
                message_id="msg-1",
                subject="Your application to Acme",
                sender="careers@acme.com",
                body="We have received your application for the SDET role.",
            )
        ]
    )

    summary = run_ingestion(db_session, gmail)

    assert summary == {
        "processed": 1,
        "ingested": 1,
        "unmatched": 0,
        "skipped_no_status": 0,
    }
    row = db_session.execute(
        text("SELECT application_id, status, source FROM status_events WHERE raw_email_id = 'msg-1'")
    ).fetchone()
    assert row.application_id == app_id
    assert row.status == "application_received"
    assert row.source == "gmail"


def test_classified_but_unmatched_email_creates_unlinked_status_event(db_session):
    # No applications tracked at all -- the matcher has nothing to match against.
    gmail = FakeGmailClient(
        [
            RawEmail(
                message_id="msg-2",
                subject="Interview Confirmation",
                sender="careers@unknown-startup.example",
                body="We would like to schedule an interview.",
            )
        ]
    )

    summary = run_ingestion(db_session, gmail)

    assert summary["ingested"] == 1
    assert summary["unmatched"] == 1
    row = db_session.execute(
        text("SELECT application_id, status FROM status_events WHERE raw_email_id = 'msg-2'")
    ).fetchone()
    assert row.application_id is None
    assert row.status == "interview_invite"


def test_unrelated_email_is_skipped_and_not_written(db_session):
    gmail = FakeGmailClient(
        [
            RawEmail(
                message_id="msg-3",
                subject="Your Amazon order has shipped",
                sender="shipment@amazon.com",
                body="Track your package here.",
            )
        ]
    )

    summary = run_ingestion(db_session, gmail)

    assert summary == {
        "processed": 1,
        "ingested": 0,
        "unmatched": 0,
        "skipped_no_status": 1,
    }
    count = db_session.execute(
        text("SELECT count(*) FROM status_events WHERE raw_email_id = 'msg-3'")
    ).scalar()
    assert count == 0


def test_reingesting_the_same_message_does_not_duplicate(db_session):
    message = RawEmail(
        message_id="msg-4",
        subject="Thank you for applying",
        sender="careers@acme.com",
        body="We have received your application.",
    )
    gmail = FakeGmailClient([message])

    first = run_ingestion(db_session, gmail)
    second = run_ingestion(db_session, gmail)  # cron re-polling overlap

    assert first["ingested"] == 1
    assert second["ingested"] == 0  # ON CONFLICT DO NOTHING -- ingested nothing new
    assert second["processed"] == 1  # still fetched/classified, just not re-written

    count = db_session.execute(
        text("SELECT count(*) FROM status_events WHERE raw_email_id = 'msg-4'")
    ).scalar()
    assert count == 1


def test_query_used_scopes_by_time_window(db_session):
    gmail = FakeGmailClient([])
    run_ingestion(db_session, gmail)
    assert gmail.queries_received == ["newer_than:2d in:inbox"]
