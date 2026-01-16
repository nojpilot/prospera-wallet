from __future__ import annotations

from aiogram.types import Message


def get_args(message: Message) -> list[str]:
    if not message.text:
        return []
    parts = message.text.split()
    if len(parts) <= 1:
        return []
    return parts[1:]
