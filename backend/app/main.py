from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

app = FastAPI(title="Job Application Tracker")


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    # A round-trip, not a hardcoded 200 -- a health check that can't
    # see the DB is down isn't worth having.
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
