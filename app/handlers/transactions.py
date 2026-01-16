from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.session import async_session_factory
from app.handlers.utils import get_args
from app.services.categories import get_or_create_category
from app.services.transactions import create_expense, create_income
from app.services.users import ensure_user
from app.services.utils import format_minor, normalize_currency, parse_amount_to_minor
from app.services.wallets import get_default_wallet
from app.services.workspaces import get_active_workspace

router = Router()


def _parse_amount_currency(args: list[str], default_currency: str) -> tuple[int, str, int]:
    if not args:
        raise ValueError("Missing amount")
    amount_raw = args[0]
    currency = default_currency
    idx = 1
    if len(args) >= 2 and len(args[1]) == 3 and args[1].isalpha():
        currency = normalize_currency(args[1])
        idx = 2
    amount_minor = parse_amount_to_minor(amount_raw, currency)
    if amount_minor <= 0:
        raise ValueError("Amount must be positive")
    return amount_minor, currency, idx


@router.message(Command("add"))
async def add_expense(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    if len(args) < 2:
        await message.answer("Usage: /add <amount> [CUR] <category> [note]")
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return

        try:
            amount_minor, currency, idx = _parse_amount_currency(
                args, workspace.base_currency
            )
        except ValueError:
            await message.answer("Invalid amount. Example: /add 250 cafe")
            return

        if len(args) <= idx:
            await message.answer("Category is required.")
            return

        category_name = args[idx]
        note = " ".join(args[idx + 1 :]) or None

        wallet = await get_default_wallet(session, workspace, user, currency)
        if wallet is None:
            await message.answer(
                f"No wallet in {currency}. Create one with /wallet_add."
            )
            return

        category = await get_or_create_category(session, workspace, category_name, "expense")
        tx = await create_expense(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=amount_minor,
            currency=currency,
            note=note,
            payer=user,
            category_id=category.id,
        )

    await message.answer(
        f"Expense added: {category.name} {format_minor(tx.amount_minor, tx.currency)}."
    )


@router.message(Command("income"))
async def add_income(message: Message) -> None:
    if message.from_user is None:
        return
    args = get_args(message)
    if len(args) < 2:
        await message.answer("Usage: /income <amount> [CUR] <category> [note]")
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return

        try:
            amount_minor, currency, idx = _parse_amount_currency(
                args, workspace.base_currency
            )
        except ValueError:
            await message.answer("Invalid amount. Example: /income 1000 salary")
            return

        if len(args) <= idx:
            await message.answer("Category is required.")
            return

        category_name = args[idx]
        note = " ".join(args[idx + 1 :]) or None

        wallet = await get_default_wallet(session, workspace, user, currency)
        if wallet is None:
            await message.answer(
                f"No wallet in {currency}. Create one with /wallet_add."
            )
            return

        category = await get_or_create_category(session, workspace, category_name, "income")
        tx = await create_income(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=amount_minor,
            currency=currency,
            note=note,
            recipient=user,
            category_id=category.id,
        )

    await message.answer(
        f"Income added: {category.name} {format_minor(tx.amount_minor, tx.currency)}."
    )
