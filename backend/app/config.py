from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://jobtracker:jobtracker_dev_pw@localhost:5432/jobtracker"


@lru_cache
def get_settings() -> Settings:
    return Settings()
