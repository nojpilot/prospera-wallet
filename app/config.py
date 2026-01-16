from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    log_level: str
    webapp_url: str
    webapp_host: str
    webapp_port: int


def _load_env() -> None:
    load_dotenv()


def get_database_url() -> str:
    _load_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")
    return database_url


def load_settings() -> Settings:
    _load_env()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    webapp_url = os.getenv("WEBAPP_URL", "")
    webapp_host = os.getenv("WEBAPP_HOST", "0.0.0.0")
    webapp_port_raw = os.getenv("WEBAPP_PORT", "8080")
    try:
        webapp_port = int(webapp_port_raw)
    except ValueError as exc:
        raise RuntimeError("WEBAPP_PORT must be an integer") from exc
    return Settings(
        bot_token=bot_token,
        database_url=get_database_url(),
        log_level=log_level,
        webapp_url=webapp_url,
        webapp_host=webapp_host,
        webapp_port=webapp_port,
    )
