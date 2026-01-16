from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Membership, Transaction, Workspace
from app.services.utils import display_name, format_minor


def _build_name_map(memberships: list[Membership]) -> dict[int, str]:
    name_map: dict[int, str] = {}
    for membership in memberships:
        if membership.user:
            name_map[membership.user_id] = display_name(membership.user)
        else:
            name_map[membership.user_id] = f"user:{membership.user_id}"
    return name_map


async def get_workspace_members(session: AsyncSession, workspace: Workspace) -> list[Membership]:
    result = await session.execute(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.workspace_id == workspace.id)
    )
    return list(result.scalars().all())


async def calculate_balances(
    session: AsyncSession,
    workspace: Workspace,
) -> dict[str, dict[int, int]]:
    balances: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    result = await session.execute(
        select(Transaction)
        .options(selectinload(Transaction.splits))
        .where(
            Transaction.workspace_id == workspace.id,
            Transaction.type == "expense",
        )
    )
    transactions = result.scalars().all()
    for tx in transactions:
        payer_id = tx.created_by
        if payer_id is None:
            continue
        for split in tx.splits:
            if split.user_id == payer_id:
                continue
            balances[tx.currency][payer_id] += split.amount_minor
            balances[tx.currency][split.user_id] -= split.amount_minor
    return balances


def format_balance_report(
    balances: dict[str, dict[int, int]],
    members: list[Membership],
) -> str:
    if not balances:
        return "All settled or no expenses yet."

    name_map = _build_name_map(members)
    lines: list[str] = []
    for currency, currency_balances in balances.items():
        lines.append(f"{currency}:")
        has_entries = False
        for user_id, amount_minor in sorted(currency_balances.items(), key=lambda item: -item[1]):
            if amount_minor == 0:
                continue
            name = name_map.get(user_id, f"user:{user_id}")
            lines.append(f"- {name}: {format_minor(amount_minor, currency)}")
            has_entries = True
        if not has_entries:
            lines.append("- all settled")
    return "\n".join(lines)
