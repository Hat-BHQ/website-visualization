from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DailyReportRule:
    key: str
    label: str
    categories: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    min_price: Decimal | None = None
    require_qualified_target: bool = False
    # Chỉ cần khớp ít nhất một keyword.
    title_keywords_any: tuple[str, ...] = ()

    # Phải khớp toàn bộ keyword.
    title_keywords_all: tuple[str, ...] = ()

    # Chỉ cần gặp một keyword loại trừ
    # là listing bị loại.
    exclude_title_keywords: tuple[str, ...] = ()


# Tương ứng cột category/target_category của dữ liệu nghiên cứu.
QUALIFIED_TARGET_CATEGORIES = (
    "speaker",
    "speakers",
    "speaker frame",
)

EXCLUDED_CONDITIONS = ("for parts or not working",)

MIN_NEW_LISTING_PRICE = Decimal("500")


TABLE_RULES: dict[str, DailyReportRule] = {
    "table_1": DailyReportRule(
        key="table_1",
        label="Table 1",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Vintage Speakers",
            "Home Speakers & Subwoofers",
            "Speakers",
            "Vintage Stereo Receivers",
        ),
        # Chép đúng keyword của Table 1 từ Apps Script vào đây.
        title_keywords_any=(),
    ),
    "table_2": DailyReportRule(
        key="table_2",
        label="Table 2",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Amplifiers & Preamps",
            "Amplifiers & Pre-Amps",
            "Amplificateurs",
            "Vintage Amplifiers & Tube Amps",
            "Receivers",
            "Receiver",
            "Amplifier Parts & Components",
        ),
        title_keywords_any=(),
    ),
    "table_3": DailyReportRule(
        key="table_3",
        label="Table 3",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Vintage Speaker & Horn Drivers",
            "Car Speakers & Speaker Systems",
            "Woofers",
            "Speaker Boxes",
            "Speaker Mounts & Stands",
            "Other Speaker Parts & Comp",
        ),
        title_keywords_any=(),
    ),
    "table_4": DailyReportRule(
        key="table_4",
        label="Table 4",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Home Theater Systems",
            "Equalizers",
            "Other Home Stereo Components",
            "Other TV, Video & Home Audio",
            "Marine Audio",
            "Audio Cables & Interconnects",
            "Headphones",
        ),
        title_keywords_any=(),
    ),
    "table_5": DailyReportRule(
        key="table_5",
        label="Table 5",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Other Vintage Audio & Video",
            "Other Vintage A/V Parts & Accs",
            "Knobs, Jacks & Switches",
            "Cases, Covers & Skins",
        ),
        title_keywords_any=(),
    ),
    "table_6": DailyReportRule(
        key="table_6",
        label="Table 6",
        require_qualified_target=True,
        min_price=MIN_NEW_LISTING_PRICE,
        categories=(
            "Television Parts",
            "Camera & Photo Accessories",
            "Computer Cables & Connectors",
            "Cell Phones & Accessories",
            "Video Games & Consoles",
            "Others",
        ),
        title_keywords_any=(),
    ),
    "table_7": DailyReportRule(
        key="table_7",
        label="Table 7 - Ended",
        require_qualified_target=True,
        statuses=(
            "ended",
            "ended_listing",
        ),
    ),
    "table_8": DailyReportRule(
        key="table_8",
        label="Table 8 - Out of Stock",
        require_qualified_target=True,
        statuses=(
            "out_of_stock",
            "out of stock",
            "outofstock",
        ),
    ),
}


NEW_LISTING_TABLE_KEYS = (
    "table_1",
    "table_2",
    "table_3",
    "table_4",
    "table_5",
    "table_6",
)

REPORT_TABLE_KEYS = (
    "all",
    *TABLE_RULES.keys(),
)
