from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ApplicationCreate, StatusEventCreate, TargetCompanyCreate

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
    would contradict "logging an application means it's now applied".

    applied_at (if given) backdates both rows to the same timestamp --
    computed once in Python rather than left to two separate DB
    defaults, so the application and its first event can't end up a
    few milliseconds apart."""
    applied_at = data.applied_at or datetime.now(UTC)

    app_row = session.execute(
        text(
            """
            INSERT INTO applications (company, role, applied_via, job_url, created_at)
            VALUES (:company, :role, :applied_via, :job_url, :created_at)
            RETURNING id
            """
        ),
        {
            "company": data.company,
            "role": data.role,
            "applied_via": data.applied_via,
            "job_url": data.job_url,
            "created_at": applied_at,
        },
    ).fetchone()
    application_id = app_row[0]

    session.execute(
        text(
            """
            INSERT INTO status_events (application_id, status, source, created_at)
            VALUES (:application_id, 'applied', 'manual', :created_at)
            """
        ),
        {"application_id": application_id, "created_at": applied_at},
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


_EVENT_COLUMNS = "id, status, source, raw_email_id, created_at"


def get_application_events(session: Session, application_id: int) -> list[dict]:
    """Chronological (oldest first) -- a timeline reads as the story of
    the application, not a feed of most-recent-first notifications."""
    rows = session.execute(
        text(
            f"""
            SELECT {_EVENT_COLUMNS} FROM status_events
            WHERE application_id = :application_id
            ORDER BY created_at ASC, id ASC
            """
        ),
        {"application_id": application_id},
    ).fetchall()
    return [dict(row._mapping) for row in rows]


def add_status_event(
    session: Session, application_id: int, data: StatusEventCreate
) -> dict | None:
    """Manual status update on an existing application -- e.g. logging
    a rejection or interview you heard about outside Gmail. Returns
    None if application_id doesn't exist (FK violation), so the caller
    can turn that into a 404 instead of a raw 500."""
    occurred_at = data.occurred_at or datetime.now(UTC)
    row = session.execute(
        text(
            f"""
            INSERT INTO status_events (application_id, status, source, created_at)
            SELECT :application_id, :status, 'manual', :created_at
            WHERE EXISTS (SELECT 1 FROM applications WHERE id = :application_id)
            RETURNING {_EVENT_COLUMNS}
            """
        ),
        {
            "application_id": application_id,
            "status": data.status.value,
            "created_at": occurred_at,
        },
    ).fetchone()
    session.commit()
    return dict(row._mapping) if row else None


def get_unmatched_events(session: Session) -> list[dict]:
    rows = session.execute(
        text(
            f"""
            SELECT {_EVENT_COLUMNS} FROM status_events
            WHERE application_id IS NULL
            ORDER BY created_at DESC, id DESC
            """
        )
    ).fetchall()
    return [dict(row._mapping) for row in rows]


def link_event_to_application(
    session: Session, event_id: int, application_id: int
) -> dict | None:
    """Only links currently-unmatched rows (application_id IS NULL) --
    this can never silently re-point an already-matched event. See
    DESIGN.md / backend/README.md for why this narrow UPDATE doesn't
    violate status_events being append-only: it corrects the matcher's
    attribution guess, not the recorded status/timestamp/source of
    what actually happened."""
    row = session.execute(
        text(
            f"""
            UPDATE status_events
            SET application_id = :application_id
            WHERE id = :event_id AND application_id IS NULL
            RETURNING {_EVENT_COLUMNS}
            """
        ),
        {"application_id": application_id, "event_id": event_id},
    ).fetchone()
    session.commit()
    return dict(row._mapping) if row else None


_TARGET_COMPANY_COLUMNS = "id, company, tier, category, notes, created_at"


def _applied_company_names(session: Session) -> list[str]:
    rows = session.execute(text("SELECT company FROM applications")).fetchall()
    return [row[0].lower() for row in rows]


_MIN_SUBSTRING_MATCH_LENGTH = 4


def _is_already_applied(company: str, applied_names_lower: list[str]) -> bool:
    """Case-insensitive match against tracked applications, for company
    names that don't match exactly between a hand-typed target list
    and however the application actually got logged ("PAR Technology"
    vs "PAR Technology Corp").

    Short names (< 4 chars, e.g. "Olo") only match exactly, not by
    substring -- found via a real false positive while seeding the
    real target list: "Olo" (len 3) matched as a substring of
    "techn-OLO-gy" inside "R3 Technology Inc". Unlike Phase 3's Gmail
    matcher, where a false negative (missed match, lands in the
    unmatched-review queue) is far cheaper than a false positive
    (silently misattributed status history), here it's the reverse: a
    false "already applied" could make you skip a company you should
    actually apply to, so the substring heuristic needs a length floor
    the Gmail matcher didn't need."""
    company_lower = company.lower()
    for applied in applied_names_lower:
        if company_lower == applied:
            return True
        shorter, longer = sorted((company_lower, applied), key=len)
        if len(shorter) >= _MIN_SUBSTRING_MATCH_LENGTH and shorter in longer:
            return True
    return False


def list_target_companies(session: Session) -> list[dict]:
    rows = session.execute(
        text(
            f"""
            SELECT {_TARGET_COMPANY_COLUMNS} FROM target_companies
            ORDER BY tier ASC, id ASC
            """
        )
    ).fetchall()
    applied_names = _applied_company_names(session)
    targets = [dict(row._mapping) for row in rows]
    for target in targets:
        target["already_applied"] = _is_already_applied(target["company"], applied_names)
    return targets


def create_target_company(session: Session, data: TargetCompanyCreate) -> dict:
    row = session.execute(
        text(
            f"""
            INSERT INTO target_companies (company, tier, category, notes)
            VALUES (:company, :tier, :category, :notes)
            RETURNING {_TARGET_COMPANY_COLUMNS}
            """
        ),
        data.model_dump(),
    ).fetchone()
    session.commit()
    result = dict(row._mapping)
    result["already_applied"] = _is_already_applied(
        result["company"], _applied_company_names(session)
    )
    return result


def delete_target_company(session: Session, target_id: int) -> bool:
    result = session.execute(
        text("DELETE FROM target_companies WHERE id = :id"), {"id": target_id}
    )
    session.commit()
    return result.rowcount > 0
