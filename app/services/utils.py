from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.db.models import User


CURRENCY_DECIMALS = {
    "JPY": 0,
    "KRW": 0,
    "VND": 0,
}


def normalize_currency(code: str) -> str:
    return code.strip().upper()


def parse_amount_to_minor(amount_raw: str, currency: str) -> int:
    decimals = CURRENCY_DECIMALS.get(currency, 2)
    cleaned = amount_raw.replace(",", ".")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc

    scale = Decimal(10) ** decimals
    minor = (value * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(minor)


def format_minor(amount_minor: int, currency: str) -> str:
    decimals = CURRENCY_DECIMALS.get(currency, 2)
    scale = Decimal(10) ** decimals
    value = Decimal(amount_minor) / scale
    if decimals == 0:
        formatted = f"{int(value)}"
    else:
        formatted = f"{value:.{decimals}f}"
    return f"{formatted} {currency}"


def display_name(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    name_parts = [part for part in [user.first_name, user.last_name] if part]
    if name_parts:
        return " ".join(name_parts)
    return f"user:{user.tg_id}"
