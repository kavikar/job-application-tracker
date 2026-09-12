from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://jobtracker:jobtracker_dev_pw@localhost:5432/jobtracker"

    # Comma-separated, not a JSON list -- simpler to set as a single
    # Render/GitHub env var string. The frontend and backend are
    # always different origins (Vercel vs Render in prod, :5173 vs
    # :8000 in dev), so this isn't a dev-only convenience.
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # MUST be overridden via env var in any real deployment -- this
    # default only exists so local dev/tests don't need a .env entry
    # for something that isn't a secret until it's actually deployed.
    api_key: str = "dev-only-change-me"

    # Only required to actually call the Gmail API (POST /ingest in
    # production). Left blank by default so nothing else in the app
    # breaks without them -- tests never touch real Gmail, so they
    # never need these set.
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
