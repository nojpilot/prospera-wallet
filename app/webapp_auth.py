from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from urllib.parse import parse_qsl


class WebAppAuthError(Exception):
    pass


def validate_init_data(init_data: str, bot_token: str) -> dict[str, str]:
    if not init_data:
        raise WebAppAuthError("Missing init data")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise WebAppAuthError("Missing hash")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data.items())
    )
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise WebAppAuthError("Invalid hash")
    return data


def extract_user(data: dict[str, str]) -> dict[str, Any]:
    raw_user = data.get("user")
    if not raw_user:
        raise WebAppAuthError("Missing user payload")
    try:
        payload = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise WebAppAuthError("Invalid user payload") from exc
    return payload
