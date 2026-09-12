from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import repositories
from app.db import get_db
from app.gmail_client import GmailClient, get_gmail_client
from app.ingestion import run_ingestion
from app.schemas import ApplicationCreate, ApplicationOut, LinkEventRequest, StatusEventOut

app = FastAPI(title="Job Application Tracker")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    # A round-trip, not a hardcoded 200 -- a health check that can't
    # see the DB is down isn't worth having.
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}


@app.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> dict:
    return repositories.create_application(db, payload)


@app.get("/applications", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)) -> list[dict]:
    return repositories.list_applications(db)


@app.post("/ingest")
def ingest(
    db: Session = Depends(get_db), gmail: GmailClient = Depends(get_gmail_client)
) -> dict:
    return run_ingestion(db, gmail)


@app.get("/applications/{application_id}/events", response_model=list[StatusEventOut])
def get_application_events(application_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return repositories.get_application_events(db, application_id)


@app.get("/events/unmatched", response_model=list[StatusEventOut])
def get_unmatched_events(db: Session = Depends(get_db)) -> list[dict]:
    return repositories.get_unmatched_events(db)


@app.patch("/events/{event_id}/link", response_model=StatusEventOut)
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
