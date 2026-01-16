from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.session import async_session_factory
from app.handlers.utils import get_args
from app.services.users import ensure_user
from app.services.utils import normalize_currency
from app.services.wallets import (
    create_wallet,
    get_wallet_by_name,
    list_wallets,
)
from app.services.workspaces import get_active_workspace

router = Router()


@router.message(Command("wallets"))
async def list_wallets_command(message: Message) -> None:
    if message.from_user is None:
        return
    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        wallets = await list_wallets(session, workspace)

    if not wallets:
        await message.answer("No wallets yet. Use /wallet_add.")
        return

    lines = ["Wallets:"]
    for wallet in wallets:
        owner = "" if wallet.owner_user_id is None else f" (owner {wallet.owner_user_id})"
        lines.append(
            f"- {wallet.name} [{wallet.type}] {wallet.currency}{owner}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("wallet_add"))
async def add_wallet_command(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    if len(args) < 2:
        await message.answer(
            "Usage: /wallet_add <name> <currency> [shared|personal]"
        )
        return

    name = args[0]
    currency = normalize_currency(args[1])
    wallet_type = args[2].lower() if len(args) >= 3 else "shared"
    if wallet_type not in {"shared", "personal"}:
        await message.answer("Wallet type must be shared or personal.")
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        existing = await get_wallet_by_name(session, workspace, name)
        if existing:
            await message.answer("Wallet with this name already exists.")
            return
        owner_id = user.id if wallet_type == "personal" else None
        wallet = await create_wallet(
            session,
            workspace,
            name=name,
            wallet_type=wallet_type,
            currency=currency,
            owner_user_id=owner_id,
        )

    await message.answer(
        f"Wallet created: {wallet.name} [{wallet.type}] {wallet.currency}."
    )
