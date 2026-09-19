from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.statuses import Status

Tier = Literal["A", "B", "C", "D"]


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


class TargetCompanyCreate(BaseModel):
    company: str = Field(min_length=1)
    tier: Tier
    category: str | None = None
    notes: str | None = None


class TargetCompanyOut(BaseModel):
    id: int
    company: str
    tier: Tier
    category: str | None
    notes: str | None
    created_at: datetime
    # Computed by cross-referencing the applications table (case-
    # insensitive substring match), not a stored column -- see
    # repositories.py. Whether you've applied is a fact that lives in
    # applications/status_events; this table shouldn't have its own,
    # separately-mutable copy of it.
    already_applied: bool
