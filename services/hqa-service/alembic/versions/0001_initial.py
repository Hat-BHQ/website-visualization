"""initial hqa schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

MARKETPLACES = ("ebay", "reverb", "etsy")
SYSTEM_SCHEMA = "hqa_system"


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _schema(name: str) -> str | None:
    return name


def _table_ref(schema: str, table_name: str) -> str:
    return f"{schema}.{table_name}"


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(JSONB, "postgresql")


def _create_schemas() -> None:
    if not _is_postgres():
        return
    for schema in (SYSTEM_SCHEMA, *MARKETPLACES):
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))


def _drop_schemas() -> None:
    if not _is_postgres():
        return
    op.execute(sa.text("DROP EXTENSION IF EXISTS pg_trgm"))
    for schema in reversed((SYSTEM_SCHEMA, *MARKETPLACES)):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


def _create_system_tables() -> None:
    system_schema = _schema(SYSTEM_SCHEMA)
    op.create_table(
        "research_targets",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("product_code", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("target_category", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_targets")),
        sa.UniqueConstraint("product_code", name=op.f("uq_research_targets_product_code")),
        schema=system_schema,
    )
    op.create_index(op.f("ix_research_targets_product_code"), "research_targets", ["product_code"], unique=False, schema=system_schema)

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("marketplace", sa.String(length=20), nullable=False),
        sa.Column("trigger_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_source_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("unchanged_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_rows", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_jobs")),
        sa.CheckConstraint("marketplace IN ('ebay', 'reverb', 'etsy')", name=op.f("ck_sync_jobs_marketplace")),
        schema=system_schema,
    )
    op.create_index(op.f("ix_sync_jobs_marketplace"), "sync_jobs", ["marketplace"], unique=False, schema=system_schema)
    op.create_index(op.f("ix_sync_jobs_trigger_type"), "sync_jobs", ["trigger_type"], unique=False, schema=system_schema)
    op.create_index(op.f("ix_sync_jobs_status"), "sync_jobs", ["status"], unique=False, schema=system_schema)
    op.create_index(op.f("ix_sync_jobs_requested_by_user_id"), "sync_jobs", ["requested_by_user_id"], unique=False, schema=system_schema)

    op.create_table(
        "sync_errors",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("sync_job_id", sa.Uuid(), sa.ForeignKey(f"{_table_ref(SYSTEM_SCHEMA, 'sync_jobs')}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace", sa.String(length=20), nullable=False),
        sa.Column("source_sheet", sa.Text(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("external_listing_id", sa.Text(), nullable=True),
        sa.Column("processing_stage", sa.Text(), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("raw_row", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_errors")),
        sa.CheckConstraint("marketplace IN ('ebay', 'reverb', 'etsy')", name=op.f("ck_sync_errors_marketplace")),
        schema=system_schema,
    )
    op.create_index(op.f("ix_sync_errors_sync_job_id"), "sync_errors", ["sync_job_id"], unique=False, schema=system_schema)
    op.create_index(op.f("ix_sync_errors_marketplace"), "sync_errors", ["marketplace"], unique=False, schema=system_schema)


def _create_listing_tables(marketplace: str, seller_column: str | None, extra_columns: list[sa.Column]) -> None:
    schema = _schema(marketplace)
    listing_name = "listings"
    match_name = "listing_matches"
    snapshot_name = "listing_snapshots"
    search_name = "search_runs"
    title_index = f"ix_{marketplace}_listings_title_trgm"

    research_target_fk = [sa.ForeignKey(f"{_table_ref(SYSTEM_SCHEMA, 'research_targets')}.id", ondelete="CASCADE")] if _is_postgres() else []
    search_target_fk = [sa.ForeignKey(f"{_table_ref(SYSTEM_SCHEMA, 'research_targets')}.id", ondelete="SET NULL")] if _is_postgres() else []

    op.create_table(
        listing_name,
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("external_listing_id", sa.Text(), nullable=False),
        sa.Column("listing_title", sa.Text(), nullable=False),
        sa.Column("listing_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("listing_location", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Text(), nullable=True),
        sa.Column("category_name", sa.Text(), nullable=True),
        sa.Column("condition_id", sa.Text(), nullable=True),
        sa.Column("condition_name", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("shipping_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("listing_views", sa.BigInteger(), nullable=True),
        sa.Column("listing_status", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("state_hash", sa.Text(), nullable=True),
        sa.Column("raw_payload", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *extra_columns,
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{marketplace}_listings")),
        sa.UniqueConstraint("external_listing_id", name=op.f(f"uq_{marketplace}_listings_external_listing_id")),
        schema=schema,
    )
    op.create_index(op.f(f"ix_{marketplace}_listings_external_listing_id"), listing_name, ["external_listing_id"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listings_listing_title"), listing_name, ["listing_title"], unique=False, schema=schema)
    op.create_index(op.f(title_index), listing_name, ["listing_title"], unique=False, schema=schema, postgresql_using="gin", postgresql_ops={"listing_title": "gin_trgm_ops"})
    op.create_index(op.f(f"ix_{marketplace}_listings_published_at"), listing_name, ["published_at"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listings_current_price"), listing_name, ["current_price"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listings_listing_status"), listing_name, ["listing_status"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listings_first_seen_at"), listing_name, ["first_seen_at"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listings_last_seen_at"), listing_name, ["last_seen_at"], unique=False, schema=schema)
    if seller_column:
        op.create_index(op.f(f"ix_{marketplace}_listings_{seller_column}"), listing_name, [seller_column], unique=False, schema=schema)

    op.create_table(
        match_name,
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("research_target_id", sa.Uuid(), *research_target_fk, nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("match_type", sa.Text(), nullable=True),
        sa.Column("exclude_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_confidence", sa.Numeric(8, 4), nullable=True),
        sa.Column("research_date", sa.Date(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{marketplace}_listing_matches")),
        sa.UniqueConstraint("listing_id", "research_target_id", "keyword", "research_date", name=op.f(f"uq_{marketplace}_listing_matches_dedupe")),
        schema=schema,
    )
    op.create_index(op.f(f"ix_{marketplace}_listing_matches_listing_id"), match_name, ["listing_id"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listing_matches_research_target_id"), match_name, ["research_target_id"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listing_matches_keyword"), match_name, ["keyword"], unique=False, schema=schema)

    op.create_table(
        snapshot_name,
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("shipping_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("listing_views", sa.BigInteger(), nullable=True),
        sa.Column("listing_status", sa.Text(), nullable=True),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("state_hash", sa.Text(), nullable=False),
        sa.Column("raw_payload", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{marketplace}_listing_snapshots")),
        sa.ForeignKeyConstraint(["listing_id"], [f"{_table_ref(schema, listing_name)}.id"], ondelete="CASCADE", name=op.f(f"fk_{marketplace}_listing_snapshots_listing_id")),
        schema=schema,
    )
    op.create_index(op.f(f"ix_{marketplace}_listing_snapshots_listing_id"), snapshot_name, ["listing_id"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_listing_snapshots_observed_at"), snapshot_name, ["observed_at"], unique=False, schema=schema)

    op.create_table(
        search_name,
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("research_target_id", sa.Uuid(), *search_target_fk, nullable=True),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("research_date", sa.Date(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("api_status", sa.Text(), nullable=True),
        sa.Column("total_results", sa.BigInteger(), nullable=True),
        sa.Column("source_limit", sa.Integer(), nullable=True),
        sa.Column("source_offset", sa.Integer(), nullable=True),
        sa.Column("response_metadata", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{marketplace}_search_runs")),
        schema=schema,
    )
    op.create_index(op.f(f"ix_{marketplace}_search_runs_research_target_id"), search_name, ["research_target_id"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_search_runs_keyword"), search_name, ["keyword"], unique=False, schema=schema)
    op.create_index(op.f(f"ix_{marketplace}_search_runs_research_date"), search_name, ["research_date"], unique=False, schema=schema)


def upgrade() -> None:
    _create_schemas()
    _create_system_tables()
    _create_listing_tables("ebay", "seller_name", [sa.Column("seller_name", sa.Text(), nullable=True), sa.Column("buying_options", _json_type(), nullable=True), sa.Column("status_reason", sa.Text(), nullable=True), sa.Column("last_status_checked_at", sa.DateTime(timezone=True), nullable=True)])
    _create_listing_tables("reverb", "shop_name", [sa.Column("shop_name", sa.Text(), nullable=True)])
    _create_listing_tables("etsy", "shop_name", [sa.Column("shop_id", sa.Text(), nullable=True), sa.Column("shop_name", sa.Text(), nullable=True), sa.Column("taxonomy_id", sa.Text(), nullable=True), sa.Column("etsy_data", _json_type(), nullable=True)])


def downgrade() -> None:
    for marketplace in reversed(MARKETPLACES):
        schema = _schema(marketplace)
        op.drop_index(op.f(f"ix_{marketplace}_search_runs_research_date"), table_name="search_runs", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_search_runs_keyword"), table_name="search_runs", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_search_runs_research_target_id"), table_name="search_runs", schema=schema)
        op.drop_table("search_runs", schema=schema)

        op.drop_index(op.f(f"ix_{marketplace}_listing_snapshots_observed_at"), table_name="listing_snapshots", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listing_snapshots_listing_id"), table_name="listing_snapshots", schema=schema)
        op.drop_table("listing_snapshots", schema=schema)

        op.drop_index(op.f(f"ix_{marketplace}_listing_matches_keyword"), table_name="listing_matches", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listing_matches_research_target_id"), table_name="listing_matches", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listing_matches_listing_id"), table_name="listing_matches", schema=schema)
        op.drop_table("listing_matches", schema=schema)

        op.drop_index(op.f(f"ix_{marketplace}_listings_last_seen_at"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_first_seen_at"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_listing_status"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_current_price"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_published_at"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_listing_title"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_listing_title_trgm"), table_name="listings", schema=schema)
        op.drop_index(op.f(f"ix_{marketplace}_listings_external_listing_id"), table_name="listings", schema=schema)
        op.drop_table("listings", schema=schema)

    op.drop_index(op.f("ix_sync_errors_marketplace"), table_name="sync_errors", schema=_schema(SYSTEM_SCHEMA))
    op.drop_index(op.f("ix_sync_errors_sync_job_id"), table_name="sync_errors", schema=_schema(SYSTEM_SCHEMA))
    op.drop_table("sync_errors", schema=_schema(SYSTEM_SCHEMA))

    op.drop_index(op.f("ix_sync_jobs_requested_by_user_id"), table_name="sync_jobs", schema=_schema(SYSTEM_SCHEMA))
    op.drop_index(op.f("ix_sync_jobs_status"), table_name="sync_jobs", schema=_schema(SYSTEM_SCHEMA))
    op.drop_index(op.f("ix_sync_jobs_trigger_type"), table_name="sync_jobs", schema=_schema(SYSTEM_SCHEMA))
    op.drop_index(op.f("ix_sync_jobs_marketplace"), table_name="sync_jobs", schema=_schema(SYSTEM_SCHEMA))
    op.drop_table("sync_jobs", schema=_schema(SYSTEM_SCHEMA))

    op.drop_index(op.f("ix_research_targets_product_code"), table_name="research_targets", schema=_schema(SYSTEM_SCHEMA))
    op.drop_table("research_targets", schema=_schema(SYSTEM_SCHEMA))
    _drop_schemas()
