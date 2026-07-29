from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import re


def normalize_header(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def get_google_credentials(oauth_token_file: str) -> Credentials:
    """
    Đọc OAuth credentials từ token JSON và tự refresh access token
    bằng refresh token khi cần.
    """

    if not oauth_token_file:
        raise ValueError("GOOGLE_OAUTH_TOKEN_FILE is required")

    token_path = Path(oauth_token_file)

    if not token_path.is_file():
        raise FileNotFoundError(f"OAuth token file not found: {oauth_token_file}")

    credentials = Credentials.from_authorized_user_file(
        str(token_path),
        SCOPES,
    )

    if credentials.expired:
        if not credentials.refresh_token:
            raise RuntimeError(
                "Google OAuth token đã hết hạn nhưng không có refresh token. "
                "Hãy chạy lại generate_google_token.py."
            )

        credentials.refresh(Request())

    if not credentials.valid:
        raise RuntimeError(
            "Google OAuth token không hợp lệ hoặc đã bị thu hồi. "
            "Hãy chạy lại generate_google_token.py."
        )

    return credentials


def read_sheet_rows(
    spreadsheet_id: str,
    oauth_token_file: str,
    sheet_name: str,
) -> list[dict[str, str]]:
    """
    Đọc toàn bộ dữ liệu trong một tab Google Sheet
    và chuyển từng dòng thành dictionary.
    """

    if not spreadsheet_id:
        raise ValueError("GOOGLE_SPREADSHEET_ID is required")

    if not sheet_name:
        raise ValueError("Google Sheet name is required")

    credentials = get_google_credentials(oauth_token_file)

    service = build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )

    # Bao tên sheet trong dấu nháy để hỗ trợ tên có khoảng trắng.
    safe_sheet_name = sheet_name.replace("'", "''")
    range_name = f"'{safe_sheet_name}'"

    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        )
        .execute()
    )

    values = response.get("values", [])

    if not values:
        return []

    headers = [normalize_header(item) for item in values[0]]

    if not any(headers):
        return []

    rows: list[dict[str, str]] = []

    for raw_row in values[1:]:
        row: dict[str, str] = {}

        for index, header in enumerate(headers):
            # Bỏ qua cột không có header
            if not header:
                continue

            value = str(raw_row[index]).strip() if index < len(raw_row) else ""

            row[header] = value

        # Không thêm dòng hoàn toàn trống
        if any(value for value in row.values()):
            rows.append(row)

    return rows
