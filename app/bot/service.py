from __future__ import annotations

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException

from app.bot import build_dispatcher, create_bot
from app.core.config import get_settings

settings = get_settings()
bot = create_bot(settings.bot_token)
dp = build_dispatcher()

app = FastAPI(title="Prospera Telegram Bot")


@app.post(settings.bot_webhook_path)
async def telegram_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != settings.bot_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    await dp.feed_update(bot, Update.model_validate(update))
    return {"ok": True}


@app.on_event("startup")
async def startup_event():
    base_url = (settings.bot_webhook_url or "http://localhost:8001").rstrip("/")
    webhook_url = f"{base_url}{settings.bot_webhook_path}"
    await bot.set_webhook(webhook_url, secret_token=settings.bot_webhook_secret)


@app.on_event("shutdown")
async def shutdown_event():
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
