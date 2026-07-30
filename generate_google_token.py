from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

CLIENT_FILE = Path("secrets/google-oauth-client.json")
TOKEN_FILE = Path("secrets/google-oauth-token.json")


def main() -> None:
    if not CLIENT_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy OAuth client: {CLIENT_FILE}")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_FILE),
        SCOPES,
    )

    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        access_type="offline",
        prompt="consent",
    )

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    print(f"Đã tạo token: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
