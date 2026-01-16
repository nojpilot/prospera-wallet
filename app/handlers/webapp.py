from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from app.config import load_settings

router = Router()


@router.message(Command("open"))
async def open_webapp(message: Message) -> None:
    settings = load_settings()
    if not settings.webapp_url:
        await message.answer("WEBAPP_URL is not configured.")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Open app", web_app=WebAppInfo(url=settings.webapp_url))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Tap to open the app.", reply_markup=keyboard)
