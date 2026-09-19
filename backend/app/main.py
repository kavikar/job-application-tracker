from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repositories
from app.auth import require_api_key
from app.config import get_settings
from app.db import get_db
from app.gmail_client import GmailClient, get_gmail_client
from app.ingestion import run_ingestion
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    LinkEventRequest,
    StatusEventCreate,
    StatusEventOut,
)

app = FastAPI(title="Job Application Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in get_settings().cors_allowed_origins.split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    # A round-trip, not a hardcoded 200 -- a health check that can't
    # see the DB is down isn't worth having. Deliberately NOT behind
    # require_api_key: a health check is meant to be checkable without
    # credentials, and it leaks nothing beyond "the DB is reachable".
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}


# Everything else needs the API key -- set once at router level rather
# than repeated on every route, so a new route added later is
# protected by default instead of needing to remember to add it.
protected = APIRouter(dependencies=[Depends(require_api_key)])


@protected.post(
    "/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED
)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> dict:
    return repositories.create_application(db, payload)


@protected.get("/applications", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)) -> list[dict]:
    return repositories.list_applications(db)


@protected.post("/ingest")
def ingest(
    db: Session = Depends(get_db), gmail: GmailClient = Depends(get_gmail_client)
) -> dict:
    return run_ingestion(db, gmail)


@protected.get("/applications/{application_id}/events", response_model=list[StatusEventOut])
def get_application_events(application_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return repositories.get_application_events(db, application_id)


@protected.post(
    "/applications/{application_id}/events",
    response_model=StatusEventOut,
    status_code=status.HTTP_201_CREATED,
)
def add_status_event(
    application_id: int, payload: StatusEventCreate, db: Session = Depends(get_db)
) -> dict:
    result = repositories.add_status_event(db, application_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@protected.get("/events/unmatched", response_model=list[StatusEventOut])
def get_unmatched_events(db: Session = Depends(get_db)) -> list[dict]:
    return repositories.get_unmatched_events(db)


@protected.patch("/events/{event_id}/link", response_model=StatusEventOut)
def link_event(
    event_id: int, payload: LinkEventRequest, db: Session = Depends(get_db)
) -> dict:
    try:
        result = repositories.link_event_to_application(db, event_id, payload.application_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=404, detail="Application not found")
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found or already linked")
    return result


app.include_router(protected)
