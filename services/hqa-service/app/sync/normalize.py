from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

UTC = timezone.utc
GOOGLE_EPOCH = datetime(1899, 12, 30, tzinfo=UTC)


def _pick(row: dict[str, str], keys: list[str]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            return cleaned
    return None


def safe_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def safe_bool(value: str | bool | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return None


def normalize_external_id(value: str | None) -> str | None:
    text = safe_text(value)
    if text is None:
        return None
    if text.endswith(".0"):
        integer_part = text[:-2]
        if integer_part.isdigit():
            return integer_part
    return text


def safe_decimal(value: str | int | float | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_google_serial_date(value: str | None) -> date | None:
    text = safe_text(value)
    if text is None:
        return None
    try:
        serial = Decimal(text)
    except InvalidOperation:
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            return None
    whole_days = int(serial)
    return (GOOGLE_EPOCH + timedelta(days=whole_days)).date()


def parse_etsy_unix_timestamp(value: str | None) -> datetime | None:
    text = safe_text(value)
    if text is None:
        return None
    try:
        timestamp = int(float(text))
    except ValueError:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)


def parse_datetime(value: str | None) -> datetime | None:
    text = safe_text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def to_marketplace_datetime(marketplace: str, row: dict[str, str]) -> datetime | None:
    if marketplace == "etsy":
        unix_dt = parse_etsy_unix_timestamp(_pick(row, ["etsy_unix_timestamp", "unix_timestamp", "timestamp", "created_timestamp"]))
        if unix_dt is not None:
            return unix_dt

    explicit_dt = parse_datetime(_pick(row, ["published_at", "published_datetime", "created_at", "datetime"]))
    if explicit_dt is not None:
        return explicit_dt

    serial_date = parse_google_serial_date(_pick(row, ["published_date", "research_date", "date"]))
    if serial_date is None:
        return None
    return datetime.combine(serial_date, datetime.min.time()).replace(tzinfo=UTC)


def build_state_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_listing_row(marketplace: str, row: dict[str, str]) -> dict:
    external_listing_id = normalize_external_id(
        _pick(row, ["external_listing_id", "listing_id", "id", "item_id", "Item ID", "ID"])
    )
    listing_title = safe_text(_pick(row, ["listing_title", "title", "name"]))
    listing_url = safe_text(_pick(row, ["listing_url", "url", "listing_link"]))

    if not external_listing_id or not listing_title or not listing_url:
        raise ValueError("Missing required listing fields")

    published_at = to_marketplace_datetime(marketplace, row)
    price = safe_decimal(_pick(row, ["current_price", "price", "item_price"]))
    shipping_price = safe_decimal(_pick(row, ["shipping_price", "shipping"]))
    total_price = safe_decimal(_pick(row, ["total_price", "price_total"]))
    if total_price is None and price is not None and shipping_price is not None:
        total_price = price + shipping_price

    listing_views_raw = _pick(row, ["listing_views", "views", "view_count"])
    listing_views = int(float(listing_views_raw)) if listing_views_raw else None

    base_payload = {
        "external_listing_id": external_listing_id,
        "listing_title": listing_title,
        "listing_url": listing_url,
        "published_at": published_at,
        "listing_location": safe_text(_pick(row, ["listing_location", "location"])),
        "country_code": safe_text(_pick(row, ["country_code", "country"])),
        "category_id": safe_text(_pick(row, ["category_id"])),
        "category_name": safe_text(_pick(row, ["category_name", "category"])),
        "condition_id": safe_text(_pick(row, ["condition_id"])),
        "condition_name": safe_text(_pick(row, ["condition_name", "condition"])),
        "image_url": safe_text(_pick(row, ["image_url", "image"])),
        "current_price": price,
        "shipping_price": shipping_price,
        "total_price": total_price,
        "currency": safe_text(_pick(row, ["currency"])),
        "listing_views": listing_views,
        "listing_status": safe_text(_pick(row, ["listing_status", "status"])) or "active",
        "raw_payload": row,
    }

    if marketplace == "ebay":
        base_payload["seller_name"] = safe_text(_pick(row, ["seller_name", "seller"]))
        base_payload["status_reason"] = safe_text(_pick(row, ["status_reason"]))
        base_payload["buying_options"] = {"buy_it_now": safe_bool(_pick(row, ["buy_it_now"]))}
    elif marketplace == "reverb":
        base_payload["shop_name"] = safe_text(_pick(row, ["shop_name", "seller_name", "seller"]))
    elif marketplace == "etsy":
        base_payload["shop_id"] = safe_text(_pick(row, ["shop_id"]))
        base_payload["shop_name"] = safe_text(_pick(row, ["shop_name", "seller_name", "seller"]))
        base_payload["taxonomy_id"] = safe_text(_pick(row, ["taxonomy_id"]))
        base_payload["etsy_data"] = {
            "is_digital": safe_bool(_pick(row, ["is_digital"])),
            "is_handmade": safe_bool(_pick(row, ["is_handmade"])),
        }

    state_hash_payload = {
        "listing_title": base_payload["listing_title"],
        "listing_status": base_payload["listing_status"],
        "current_price": str(base_payload["current_price"] or ""),
        "shipping_price": str(base_payload["shipping_price"] or ""),
        "total_price": str(base_payload["total_price"] or ""),
        "quantity": str(row.get("quantity", "")),
    }
    base_payload["state_hash"] = build_state_hash(state_hash_payload)

    product_code = safe_text(_pick(row, ["product_code", "product_id", "sku"]))
    keyword = safe_text(_pick(row, ["keyword", "search_keyword"]))
    research_date = parse_google_serial_date(_pick(row, ["research_date", "date"]))

    return {
        "listing": base_payload,
        "target": {
            "product_code": product_code,
            "brand": safe_text(_pick(row, ["brand"])),
            "model": safe_text(_pick(row, ["model"])),
            "target_category": safe_text(_pick(row, ["target_category", "category"])),
        },
        "match": {
            "keyword": keyword,
            "match_type": safe_text(_pick(row, ["match_type"])) or "keyword",
            "exclude_flag": safe_bool(_pick(row, ["exclude_flag"])) or False,
            "raw_confidence": safe_decimal(_pick(row, ["raw_confidence", "confidence"])),
            "research_date": research_date,
        },
    }
