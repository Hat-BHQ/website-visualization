from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import (
    Date,
    and_,
    asc,
    case,
    cast,
    desc,
    distinct,
    exists,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import ResearchTarget
from app.repositories.hqa_repository import get_marketplace_config
from app.reporting.daily_report_rules import (
    EXCLUDED_CONDITIONS,
    NEW_LISTING_TABLE_KEYS,
    QUALIFIED_TARGET_CATEGORIES,
    TABLE_RULES,
)


STATUS_ALIASES = {
    "active": ("active",),
    "ended": (
        "ended",
        "ended_listing",
    ),
    "out_of_stock": (
        "out_of_stock",
        "out of stock",
        "outofstock",
    ),
}


def normalized(column):
    return func.lower(func.trim(func.coalesce(column, "")))


def report_at_expression(listing_model):
    """Use the same update time shown on Listings, with first-seen fallback."""
    return func.coalesce(
        listing_model.last_seen_at,
        listing_model.first_seen_at,
    )


def report_date_expression(listing_model):
    return cast(report_at_expression(listing_model), Date)


def status_condition(listing_model, statuses: tuple[str, ...]):
    normalized_statuses = tuple(value.strip().lower() for value in statuses)
    return normalized(listing_model.listing_status).in_(normalized_statuses)


def target_qualification_exists(
    *,
    listing_model,
    match_model,
    selected_date: date,
):
    """
    A listing remains qualified after the original research day.

    Previously this required match.research_date == selected_date. That made a
    status/price update disappear from a later daily report because no new match
    row was created on the update day.
    """
    return exists(
        select(1)
        .select_from(match_model)
        .join(
            ResearchTarget,
            ResearchTarget.id == match_model.research_target_id,
        )
        .where(
            match_model.listing_id == listing_model.id,
            or_(
                match_model.research_date.is_(None),
                match_model.research_date <= selected_date,
            ),
            match_model.exclude_flag.is_(False),
            normalized(ResearchTarget.target_category).in_(
                QUALIFIED_TARGET_CATEGORIES
            ),
        )
    )


def rule_condition(
    *,
    listing_model,
    match_model,
    selected_date: date,
    rule_key: str,
):
    rule = TABLE_RULES[rule_key]
    conditions = []

    if rule.require_qualified_target:
        conditions.append(
            target_qualification_exists(
                listing_model=listing_model,
                match_model=match_model,
                selected_date=selected_date,
            )
        )
        conditions.append(
            ~normalized(listing_model.condition_name).in_(EXCLUDED_CONDITIONS)
        )

    if rule.min_price is not None:
        conditions.append(listing_model.current_price > rule.min_price)

    if rule.categories:
        conditions.append(
            normalized(listing_model.category_name).in_(
                tuple(value.lower() for value in rule.categories)
            )
        )

    if rule.statuses:
        conditions.append(status_condition(listing_model, rule.statuses))

    if rule.title_keywords_any:
        conditions.append(
            or_(
                *[
                    listing_model.listing_title.ilike(f"%{keyword}%")
                    for keyword in rule.title_keywords_any
                ]
            )
        )

    if rule.title_keywords_all:
        conditions.append(
            and_(
                *[
                    listing_model.listing_title.ilike(f"%{keyword}%")
                    for keyword in rule.title_keywords_all
                ]
            )
        )

    if rule.exclude_title_keywords:
        conditions.append(
            ~or_(
                *[
                    listing_model.listing_title.ilike(f"%{keyword}%")
                    for keyword in rule.exclude_title_keywords
                ]
            )
        )

    if not conditions:
        return True

    return and_(*conditions)


def new_qualified_condition(
    *,
    listing_model,
    match_model,
    selected_date: date,
):
    return or_(
        *[
            rule_condition(
                listing_model=listing_model,
                match_model=match_model,
                selected_date=selected_date,
                rule_key=rule_key,
            )
            for rule_key in NEW_LISTING_TABLE_KEYS
        ]
    )


def empty_response(
    *,
    marketplace: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    return {
        "marketplace": marketplace,
        "selected_date": None,
        "summary": {
            "total_listings_on_selected_date": 0,
            "new_listings_qualified": 0,
            "ended_listings": 0,
            "out_of_stock": 0,
        },
        "status_options": [],
        "table_counts": [
            {"key": "all", "label": "All listings", "count": 0},
            *[
                {"key": key, "label": rule.label, "count": 0}
                for key, rule in TABLE_RULES.items()
            ],
        ],
        "items": [],
        "page": page,
        "page_size": page_size,
        "total": 0,
        "pages": 0,
    }


async def get_daily_report_data(
    session: AsyncSession,
    *,
    marketplace: str,
    selected_date: date | None,
    status_filter: list[str] | None,
    table_key: str,
    sort_by: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    config = get_marketplace_config(marketplace)
    listing_model = config["listing"]
    match_model = config["match"]

    report_at = report_at_expression(listing_model)
    report_date = report_date_expression(listing_model)

    # When the UI does not send a date, open the newest available report instead
    # of defaulting to today and returning an empty page.
    if selected_date is None:
        latest_date_result = await session.execute(
            select(func.max(report_date)).select_from(listing_model)
        )
        selected_date = latest_date_result.scalar_one_or_none()

    if selected_date is None:
        return empty_response(
            marketplace=marketplace,
            page=page,
            page_size=page_size,
        )

    report_day_condition = report_date == selected_date

    new_qualified = new_qualified_condition(
        listing_model=listing_model,
        match_model=match_model,
        selected_date=selected_date,
    )
    ended_condition = status_condition(
        listing_model,
        STATUS_ALIASES["ended"],
    )
    out_of_stock_condition = status_condition(
        listing_model,
        STATUS_ALIASES["out_of_stock"],
    )

    table_conditions = {
        key: rule_condition(
            listing_model=listing_model,
            match_model=match_model,
            selected_date=selected_date,
            rule_key=key,
        )
        for key in TABLE_RULES
    }

    summary_statement = (
        select(
            func.count(distinct(listing_model.id)).label("total"),
            func.count(
                distinct(
                    case(
                        (new_qualified, listing_model.id),
                        else_=None,
                    )
                )
            ).label("new_qualified"),
            func.count(
                distinct(
                    case(
                        (ended_condition, listing_model.id),
                        else_=None,
                    )
                )
            ).label("ended"),
            func.count(
                distinct(
                    case(
                        (out_of_stock_condition, listing_model.id),
                        else_=None,
                    )
                )
            ).label("out_of_stock"),
            *[
                func.count(
                    distinct(
                        case(
                            (condition, listing_model.id),
                            else_=None,
                        )
                    )
                ).label(key)
                for key, condition in table_conditions.items()
            ],
        )
        .select_from(listing_model)
        .where(report_day_condition)
    )
    summary_result = await session.execute(summary_statement)
    summary_row = summary_result.one()

    # Dynamic status values and counts come directly from the marketplace table,
    # matching the Listings filter rather than a hard-coded frontend list.
    status_result = await session.execute(
        select(
            listing_model.listing_status.label("value"),
            func.count(distinct(listing_model.id)).label("count"),
        )
        .where(report_day_condition)
        .group_by(listing_model.listing_status)
        .order_by(asc(listing_model.listing_status))
    )
    status_options = [
        {
            "value": row.value,
            "label": row.value,
            "count": int(row.count or 0),
        }
        for row in status_result.all()
        if row.value
    ]

    list_conditions = [report_day_condition]

    if table_key != "all" and table_key in table_conditions:
        list_conditions.append(table_conditions[table_key])

    if status_filter:
        normalized_statuses = tuple(
            value.strip().lower()
            for value in status_filter
            if value.strip()
        )
        if normalized_statuses:
            list_conditions.append(
                normalized(listing_model.listing_status).in_(normalized_statuses)
            )

    base_statement = select(
        listing_model,
        report_at.label("report_at"),
    ).where(*list_conditions)

    count_statement = select(func.count()).select_from(base_statement.subquery())
    total_result = await session.execute(count_statement)
    total = int(total_result.scalar_one() or 0)

    if sort_by == "price_desc":
        base_statement = base_statement.order_by(
            desc(listing_model.current_price).nullslast(),
            desc(listing_model.id),
        )
    elif sort_by == "price_asc":
        base_statement = base_statement.order_by(
            asc(listing_model.current_price).nullslast(),
            asc(listing_model.id),
        )
    elif sort_by == "title_asc":
        base_statement = base_statement.order_by(
            asc(listing_model.listing_title),
            asc(listing_model.id),
        )
    else:
        base_statement = base_statement.order_by(
            desc(report_at),
            desc(listing_model.id),
        )

    base_statement = base_statement.offset((page - 1) * page_size).limit(page_size)
    listing_result = await session.execute(base_statement)

    items = []
    for listing, report_at_value in listing_result.all():
        items.append(
            {
                "id": listing.id,
                "external_listing_id": listing.external_listing_id,
                "listing_title": listing.listing_title,
                "listing_url": listing.listing_url,
                "seller_name": getattr(listing, "seller_name", None),
                "shop_name": getattr(listing, "shop_name", None),
                "category_name": listing.category_name,
                "condition_name": listing.condition_name,
                "current_price": listing.current_price,
                "shipping_price": listing.shipping_price,
                "total_price": listing.total_price,
                "currency": listing.currency,
                "image_url": listing.image_url,
                "listing_status": listing.listing_status,
                "status_reason": getattr(listing, "status_reason", None),
                "published_at": listing.published_at,
                "first_seen_at": listing.first_seen_at,
                "last_seen_at": listing.last_seen_at,
                "report_at": report_at_value,
                "report_date": selected_date,
            }
        )

    table_counts = [
        {
            "key": "all",
            "label": "All listings",
            "count": int(summary_row.total or 0),
        }
    ]
    for key, rule in TABLE_RULES.items():
        table_counts.append(
            {
                "key": key,
                "label": rule.label,
                "count": int(getattr(summary_row, key) or 0),
            }
        )

    pages = (total + page_size - 1) // page_size if total else 0

    return {
        "marketplace": marketplace,
        "selected_date": selected_date,
        "summary": {
            "total_listings_on_selected_date": int(summary_row.total or 0),
            "new_listings_qualified": int(summary_row.new_qualified or 0),
            "ended_listings": int(summary_row.ended or 0),
            "out_of_stock": int(summary_row.out_of_stock or 0),
        },
        "status_options": status_options,
        "table_counts": table_counts,
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }
