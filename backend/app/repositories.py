from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ApplicationCreate

_SELECT_WITH_STATUS = """
    SELECT
        a.id, a.company, a.role, a.applied_via, a.job_url, a.created_at,
        s.status AS current_status
    FROM applications a
    JOIN application_current_status s ON s.application_id = a.id
"""


def create_application(session: Session, data: ApplicationCreate) -> dict:
    """Inserts the application and its first status_event (applied /
    manual) as one unit -- see Phase 2 test strategy in the commit
    message / chat for why: a freshly created application with zero
    events has no row in application_current_status at all, which
    would contradict "logging an application means it's now applied"."""
    app_row = session.execute(
        text(
            """
            INSERT INTO applications (company, role, applied_via, job_url)
            VALUES (:company, :role, :applied_via, :job_url)
            RETURNING id
            """
        ),
        data.model_dump(),
    ).fetchone()
    application_id = app_row[0]

    session.execute(
        text(
            """
            INSERT INTO status_events (application_id, status, source)
            VALUES (:application_id, 'applied', 'manual')
            """
        ),
        {"application_id": application_id},
    )
    session.commit()

    return get_application(session, application_id)


def get_application(session: Session, application_id: int) -> dict:
    row = session.execute(
        text(f"{_SELECT_WITH_STATUS} WHERE a.id = :id"),
        {"id": application_id},
    ).fetchone()
    return dict(row._mapping)


def list_applications(session: Session) -> list[dict]:
    rows = session.execute(
        text(f"{_SELECT_WITH_STATUS} ORDER BY a.created_at DESC")
    ).fetchall()
    return [dict(row._mapping) for row in rows]
