from fastapi import Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import repositories
from app.db import get_db
from app.gmail_client import GmailClient, get_gmail_client
from app.ingestion import run_ingestion
from app.schemas import ApplicationCreate, ApplicationOut

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
