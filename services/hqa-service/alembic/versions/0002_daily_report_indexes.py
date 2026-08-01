"""Add daily report indexes.

Revision ID: 0002_daily_report_indexes
Revises: 0001_initial
Create Date: 2026-07-31
"""

from alembic import op


revision = "0002_daily_report_indexes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


SCHEMAS = (
    "ebay",
    "reverb",
    "etsy",
)


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
            ix_{schema}_listing_matches_research_date_listing_id
            ON {schema}.listing_matches
            (research_date, listing_id)
            """
        )

        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
            ix_{schema}_listings_category_name
            ON {schema}.listings
            (category_name)
            """
        )

        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
            ix_{schema}_listings_condition_name
            ON {schema}.listings
            (condition_name)
            """
        )


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(
            f"""
            DROP INDEX IF EXISTS
            {schema}.ix_{schema}_listings_condition_name
            """
        )

        op.execute(
            f"""
            DROP INDEX IF EXISTS
            {schema}.ix_{schema}_listings_category_name
            """
        )

        op.execute(
            f"""
            DROP INDEX IF EXISTS
            {schema}.ix_{schema}_listing_matches_research_date_listing_id
            """
        )
