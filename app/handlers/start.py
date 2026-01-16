from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.db.session import async_session_factory
from app.services.users import ensure_user

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    if message.from_user is None:
        return
    async with async_session_factory() as session:
        await ensure_user(session, message.from_user)
    await message.answer("Welcome! Use /help to see commands.")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Commands:\n"
        "/start - register\n"
        "/help - this message\n"
        "/open - open web app\n"
        "/setup <name> [CUR] - create workspace\n"
        "/join <id> - join workspace\n"
        "/workspace [id] - list/switch workspace\n"
        "/wallets - list wallets\n"
        "/wallet_add <name> <CUR> [shared|personal]\n"
        "/categories [expense|income]\n"
        "/category_add <name> [expense|income]\n"
        "/add <amount> [CUR] <category> [note]\n"
        "/income <amount> [CUR] <category> [note]\n"
        "/balance - who owes whom\n"
        "/report - monthly expense report"
    )
