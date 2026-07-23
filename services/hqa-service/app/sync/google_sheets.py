from __future__ import annotations

from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


def read_sheet_rows(spreadsheet_id: str, service_account_file: str, sheet_name: str) -> list[dict[str, str]]:
    credential_path = Path(service_account_file)
    if not service_account_file:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE is required")
    if not credential_path.exists():
        raise FileNotFoundError(f"Service account file not found: {service_account_file}")

    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=sheet_name)
        .execute()
    )
    values = response.get("values", [])
    if not values:
        return []

    headers = [str(item).strip() for item in values[0]]
    rows: list[dict[str, str]] = []
    for raw_row in values[1:]:
        row: dict[str, str] = {}
        for index, header in enumerate(headers):
            row[header] = str(raw_row[index]).strip() if index < len(raw_row) else ""
        rows.append(row)
    return rows
