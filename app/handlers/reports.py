from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db.session import async_session_factory
from app.services.balance import calculate_balances, format_balance_report, get_workspace_members
from app.services.reporting import monthly_expense_report
from app.services.users import ensure_user
from app.services.workspaces import get_active_workspace

router = Router()


@router.message(Command("balance"))
async def balance_command(message: Message) -> None:
    if message.from_user is None:
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        balances = await calculate_balances(session, workspace)
        members = await get_workspace_members(session, workspace)

    await message.answer(format_balance_report(balances, members))


@router.message(Command("report"))
async def report_command(message: Message) -> None:
    if message.from_user is None:
        return

    async with async_session_factory() as session:
        user = await ensure_user(session, message.from_user)
        workspace = await get_active_workspace(session, user)
        if workspace is None:
            await message.answer("No active workspace. Use /setup or /join first.")
            return
        report = await monthly_expense_report(session, workspace)

    await message.answer(report)
