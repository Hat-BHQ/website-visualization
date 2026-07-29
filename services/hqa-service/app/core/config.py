from functools import lru_cache
from urllib.parse import urlparse
from typing import Literal
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

HQA_SCHEMAS = {
    "system": "hqa_system",
    "ebay": "ebay",
    "reverb": "reverb",
    "etsy": "etsy",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HQ Portal HQA Service"
    environment: str = "local"

    database_url: str = Field(
        default=(
            "postgresql+psycopg://hq_portal:hq_portal_password@postgres:5432/hqa_db"
        ),
        validation_alias=AliasChoices(
            "HQA_DATABASE_URL",
            "DATABASE_URL",
        ),
    )

    jwt_secret_key: str = Field(
        default="change-me-access-secret",
        alias="JWT_SECRET_KEY",
    )

    redis_url: str = Field(
        default="redis://redis:6379/0",
        alias="REDIS_URL",
    )

    auth_service_url: str = Field(
        default="http://auth-service:8000",
        alias="AUTH_SERVICE_URL",
    )

    celery_timezone: str = Field(
        default="Asia/Bangkok",
        alias="CELERY_TIMEZONE",
    )

    # Google Sheets
    google_auth_mode: Literal["oauth", "service_account"] = Field(
        default="oauth",
        alias="GOOGLE_AUTH_MODE",
    )

    google_spreadsheet_id: str = Field(
        default="",
        alias="GOOGLE_SPREADSHEET_ID",
    )

    google_oauth_client_file: str = Field(
        default="/run/secrets/google-oauth-client.json",
        alias="GOOGLE_OAUTH_CLIENT_FILE",
    )

    google_oauth_token_file: str = Field(
        default="/run/secrets/google-oauth-token.json",
        alias="GOOGLE_OAUTH_TOKEN_FILE",
    )

    # Giữ lại nếu muốn hỗ trợ cả Service Account
    google_service_account_file: str = Field(
        default="",
        alias="GOOGLE_SERVICE_ACCOUNT_FILE",
    )

    cors_origins: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    access_token_expire_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def is_sqlite_database(database_url: str) -> bool:
    return urlparse(database_url).scheme.startswith("sqlite")


def get_schema_translate_map(database_url: str) -> dict[str, str | None]:
    return {}
