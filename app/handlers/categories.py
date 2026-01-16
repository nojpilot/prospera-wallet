from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.session import async_session_factory
from app.handlers.utils import get_args
from app.services.categories import get_or_create_category, list_categories
from app.services.users import ensure_user
from app.services.workspaces import get_active_workspace

router = Router()


@router.message(Command("categories"))
async def list_categories_command(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    category_type = None
    if args:
        category_type = args[0].lower()
        if category_type not in {"expense", "income"}:
            await message.answer("Usage: /categories [expense|income]")
            return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        categories = await list_categories(session, workspace, category_type)

    if not categories:
        await message.answer("No categories yet. Use /category_add.")
        return

    lines = ["Categories:"]
    for category in categories:
        lines.append(f"- {category.name} [{category.type}]")
    await message.answer("\n".join(lines))


@router.message(Command("category_add"))
async def add_category_command(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    if not args:
        await message.answer("Usage: /category_add <name> [expense|income]")
        return

    category_type = "expense"
    if args[-1].lower() in {"expense", "income"}:
        category_type = args[-1].lower()
        name = " ".join(args[:-1])
    else:
        name = " ".join(args)

    if not name:
        await message.answer("Category name is required.")
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        category = await get_or_create_category(session, workspace, name, category_type)

    await message.answer(f"Category ready: {category.name} [{category.type}].")
