from __future__ import annotations

import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import HQA_SCHEMAS, get_schema_translate_map, get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403

config = context.config
fileConfig(config.config_file_name)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def _attach_sqlite_schemas(connectable) -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    url = make_url(settings.database_url)
    base_path = Path(url.database or "hqa.db")
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    attachment_dir = base_path.parent

    @event.listens_for(connectable.sync_engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        for schema_name in HQA_SCHEMAS.values():
            attachment_path = attachment_dir / f"{schema_name}.db"
            escaped_path = str(attachment_path).replace("'", "''")
            cursor.execute(f"ATTACH DATABASE '{escaped_path}' AS {schema_name}")
        cursor.close()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        render_as_batch=url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        execution_options={"schema_translate_map": get_schema_translate_map(settings.database_url)},
    )
    _attach_sqlite_schemas(connectable)

    async with connectable.connect() as connection:
        def do_run_migrations(sync_connection):
            context.configure(
                connection=sync_connection,
                target_metadata=target_metadata,
                include_schemas=True,
                render_as_batch=sync_connection.dialect.name == "sqlite",
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


run_migrations()
