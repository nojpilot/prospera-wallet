from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.session import async_session_factory
from app.handlers.utils import get_args
from app.services.categories import ensure_default_categories
from app.services.users import ensure_user
from app.services.utils import normalize_currency
from app.services.wallets import ensure_default_wallets
from app.services.workspaces import (
    add_member,
    create_workspace,
    get_active_workspace,
    get_workspace_by_id,
    list_user_workspaces,
    set_active_workspace,
)

router = Router()


@router.message(Command("setup"))
async def setup_workspace(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    name = "My Workspace"
    currency = "USD"
    if args:
        if len(args[-1]) == 3 and args[-1].isalpha():
            currency = normalize_currency(args[-1])
            name = " ".join(args[:-1]) or name
        else:
            name = " ".join(args)

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await create_workspace(session, user, name, currency)
        await ensure_default_wallets(session, workspace, user)
        await ensure_default_categories(session, workspace)

    await message.answer(
        "Workspace created.\n"
        f"Name: {workspace.name}\n"
        f"ID: {workspace.id}\n"
        "Invite partner with: /join <workspace_id>"
    )


@router.message(Command("join"))
async def join_workspace(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    if not args:
        await message.answer("Usage: /join <workspace_id>")
        return

    try:
        workspace_id = int(args[0])
    except ValueError:
        await message.answer("Workspace id should be a number.")
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_workspace_by_id(session, workspace_id)
        if workspace is None:
            await message.answer("Workspace not found.")
            return
        await add_member(session, workspace, user)
        await ensure_default_wallets(session, workspace, user)
        await ensure_default_categories(session, workspace)

    await message.answer(
        f"Joined workspace '{workspace.name}'. Active workspace set."
    )


@router.message(Command("workspace"))
async def workspace_command(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        if args:
            try:
                workspace_id = int(args[0])
            except ValueError:
                await message.answer("Usage: /workspace <workspace_id>")
                return

            workspace = await get_workspace_by_id(session, workspace_id)
            if workspace is None:
                await message.answer("Workspace not found.")
                return

            memberships = await list_user_workspaces(session, user)
            if workspace.id not in {ws.id for ws in memberships}:
                await message.answer("You are not a member of this workspace.")
                return

            await set_active_workspace(session, user, workspace.id)
            await message.answer(f"Active workspace set to '{workspace.name}'.")
            return

        active = await get_active_workspace(session, user)
        workspaces = await list_user_workspaces(session, user)

    if not workspaces:
        await message.answer("No workspaces yet. Use /setup to create one.")
        return

    lines = ["Your workspaces:"]
    for workspace in workspaces:
        marker = "*" if active and workspace.id == active.id else " "
        lines.append(f"{marker} {workspace.id} - {workspace.name}")
    lines.append("Use /workspace <id> to switch.")
    await message.answer("\n".join(lines))
