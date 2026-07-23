from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "HQ Portal Auth Service"
    environment: str = "local"
    database_url: str = Field(
        default="postgresql+psycopg://hq_portal:hq_portal_password@postgres:5432/auth_db",
        validation_alias=AliasChoices("AUTH_DATABASE_URL", "DATABASE_URL"),
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    jwt_secret_key: str = Field(default="change-me-access-secret", alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(default="change-me-refresh-secret", alias="JWT_REFRESH_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    refresh_token_expire_days: int = Field(
        default=30,
        validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS", "JWT_REFRESH_TOKEN_EXPIRE_DAYS"),
    )
    seed_default_password: str | None = Field(default=None, alias="SEED_DEFAULT_PASSWORD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
