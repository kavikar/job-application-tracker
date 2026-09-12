"""Orchestrates one ingestion run: fetch candidate messages, classify,
match, write status_events. The Gmail query only scopes by time
window (not by keyword) -- classify() is what decides whether a
message is job-related at all, so ingestion doesn't need a second,
separately-maintained keyword filter at the Gmail-query layer.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.classifier import classify
from app.gmail_client import GmailClient
from app.matcher import ApplicationRecord, match_application

DEFAULT_LOOKBACK_QUERY = "newer_than:2d in:inbox"


def run_ingestion(
    db: Session, gmail: GmailClient, query: str = DEFAULT_LOOKBACK_QUERY
) -> dict:
    applications = _load_applications(db)
    messages = gmail.list_recent_messages(query)

    ingested = 0
    unmatched = 0
    skipped_no_status = 0

    for message in messages:
        status = classify(message.subject, message.body, message.sender)
        if status is None:
            skipped_no_status += 1
            continue

        application = match_application(
            message.subject, message.sender, message.body, applications
        )
        if application is None:
            unmatched += 1

        result = db.execute(
            text(
                """
                INSERT INTO status_events (application_id, status, source, raw_email_id)
                VALUES (:application_id, :status, 'gmail', :raw_email_id)
                ON CONFLICT (raw_email_id) DO NOTHING
                """
            ),
            {
                "application_id": application.id if application else None,
                "status": status.value,
                "raw_email_id": message.message_id,
            },
        )
        if result.rowcount:
            ingested += 1

    db.commit()
    return {
        "processed": len(messages),
        "ingested": ingested,
        "unmatched": unmatched,
        "skipped_no_status": skipped_no_status,
    }


def _load_applications(db: Session) -> list[ApplicationRecord]:
    rows = db.execute(text("SELECT id, company, job_url FROM applications")).fetchall()
    return [
        ApplicationRecord(id=row.id, company=row.company, job_url=row.job_url)
        for row in rows
    ]
