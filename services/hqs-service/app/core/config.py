from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "HQ Portal HQS Service"
    environment: str = "local"
    database_url: str = Field(
        default="postgresql+psycopg://hq_portal:hq_portal_password@postgres:5432/hqs_db",
        validation_alias=AliasChoices("HQS_DATABASE_URL", "DATABASE_URL"),
    )
    jwt_secret_key: str = Field(default="change-me-access-secret", alias="JWT_SECRET_KEY")
    cors_origins: str = Field(default="http://localhost:8080,http://localhost:5173", alias="CORS_ORIGINS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
