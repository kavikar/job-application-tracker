from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1)
    role: str = Field(min_length=1)
    applied_via: str | None = None
    job_url: str | None = None


class ApplicationOut(BaseModel):
    id: int
    company: str
    role: str
    applied_via: str | None
    job_url: str | None
    created_at: datetime
    current_status: str
