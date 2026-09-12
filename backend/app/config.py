from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://jobtracker:jobtracker_dev_pw@localhost:5432/jobtracker"

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
