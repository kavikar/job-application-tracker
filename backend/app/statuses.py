from enum import StrEnum


class Status(StrEnum):
    """Must stay in sync with the CHECK constraint on status_events.status
    in db/migrations/0001_init.sql -- see DESIGN.md for why that's a
    CHECK constraint and not a Postgres ENUM (and therefore not
    something the DB enforces is in sync with this automatically)."""

    APPLIED = "applied"
    APPLICATION_RECEIVED = "application_received"
    INTERVIEW_INVITE = "interview_invite"
    REJECTED = "rejected"
    OFFER = "offer"
