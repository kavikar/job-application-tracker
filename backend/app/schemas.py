from datetime import datetime

from pydantic import BaseModel, Field

from app.statuses import Status


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1)
    role: str = Field(min_length=1)
    applied_via: str | None = None
    job_url: str | None = None
    # Backdates both applications.created_at and the first status_event
    # -- for logging an application you actually submitted earlier
    # (e.g. importing history), not just "right now". Omit for the
    # normal case; defaults to now().
    applied_at: datetime | None = None


class StatusEventCreate(BaseModel):
    status: Status
    # Backdates the event -- e.g. logging a rejection you received a
    # few days ago rather than right now. Omit to default to now().
    occurred_at: datetime | None = None


class ApplicationOut(BaseModel):
    id: int
    company: str
    role: str
    applied_via: str | None
    job_url: str | None
    created_at: datetime
    current_status: str


class StatusEventOut(BaseModel):
    id: int
    status: str
    source: str
    raw_email_id: str | None
    created_at: datetime


class LinkEventRequest(BaseModel):
    application_id: int
