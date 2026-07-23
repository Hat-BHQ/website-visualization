from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import Request
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import HQA_SCHEMAS, get_schema_translate_map
from app.core.config import Settings


def _attach_sqlite_schemas(engine, database_url: str) -> None:
    if not database_url.startswith("sqlite"):
        return

    url = make_url(database_url)
    base_path = Path(url.database or "hqa.db")
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    attachment_dir = base_path.parent

    @event.listens_for(engine.sync_engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        for schema_name in HQA_SCHEMAS.values():
            attachment_path = attachment_dir / f"{schema_name}.db"
            escaped_path = str(attachment_path).replace("'", "''")
            cursor.execute(f"ATTACH DATABASE '{escaped_path}' AS {schema_name}")
        cursor.close()


def create_engine(settings: Settings):
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        execution_options={"schema_translate_map": get_schema_translate_map(settings.database_url)},
    )
    _attach_sqlite_schemas(engine, settings.database_url)
    return engine


def create_sessionmaker(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session_from_app(request: Request) -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = request.app.state.sessionmaker
    async with sessionmaker() as session:
        yield session
