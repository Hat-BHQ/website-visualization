from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import jwt

from app.core.config import Settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def decode_access_token(settings: Settings, token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload
