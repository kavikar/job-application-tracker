"""Shared raw-SQL test helpers for seeding data directly, bypassing
the API. Used by both schema-level tests (Phase 1) and endpoint tests
(Phase 2+) that need to set up state the endpoint under test doesn't
itself create.
"""

from sqlalchemy import text


def insert_application(session, company="Acme", role="SDET"):
    row = session.execute(
        text(
            "INSERT INTO applications (company, role) VALUES (:company, :role) RETURNING id"
        ),
        {"company": company, "role": role},
    ).fetchone()
    session.flush()
    return row[0]


def insert_event(session, application_id, status, source, raw_email_id=None):
    session.execute(
        text(
            """
            INSERT INTO status_events (application_id, status, source, raw_email_id)
            VALUES (:application_id, :status, :source, :raw_email_id)
            """
        ),
        {
            "application_id": application_id,
            "status": status,
            "source": source,
            "raw_email_id": raw_email_id,
        },
    )
    session.flush()
