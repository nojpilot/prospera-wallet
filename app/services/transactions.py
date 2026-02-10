from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Membership,
    Transaction,
    TransactionType,
    TransactionSplit,
    User,
    Wallet,
    Workspace,
)


@dataclass(frozen=True)
class Split:
    user_id: int
    amount_minor: int


def compute_weighted_splits(amount_minor: int, memberships: list[Membership]) -> list[Split]:
    if not memberships:
        return []
    weights = [max(0, membership.share_weight) for membership in memberships]
    total_weight = sum(weights)
    if total_weight <= 0:
        weights = [1 for _ in memberships]
        total_weight = len(memberships)

    base = [amount_minor * weight // total_weight for weight in weights]
    remainder = amount_minor - sum(base)
    for idx in range(remainder):
        base[idx % len(base)] += 1

    splits = []
    for membership, amount in zip(memberships, base, strict=False):
        splits.append(Split(user_id=membership.user_id, amount_minor=amount))
    return splits


async def list_memberships(
    session: AsyncSession,
    workspace: Workspace,
) -> list[Membership]:
    result = await session.execute(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.workspace_id == workspace.id)
        .order_by(Membership.user_id)
    )
    return list(result.scalars().all())


async def create_expense(
    session: AsyncSession,
    workspace: Workspace,
    wallet: Wallet,
    amount_minor: int,
    currency: str,
    note: str | None,
    payer: User,
    category_id: int | None,
) -> Transaction:
    tx = Transaction(
        workspace_id=workspace.id,
        wallet_id=wallet.id,
        type=TransactionType.expense,
        amount_minor=amount_minor,
        currency=currency,
        note=note,
        created_by=payer.id,
        category_id=category_id,
    )
    session.add(tx)
    await session.flush()

    memberships = await list_memberships(session, workspace)
    if memberships:
        splits = compute_weighted_splits(amount_minor, memberships)
    else:
        splits = [Split(user_id=payer.id, amount_minor=amount_minor)]
    for split in splits:
        session.add(
            TransactionSplit(
                transaction_id=tx.id,
                user_id=split.user_id,
                amount_minor=split.amount_minor,
            )
        )

    await session.commit()
    await session.refresh(tx)
    return tx


async def create_income(
    session: AsyncSession,
    workspace: Workspace,
    wallet: Wallet,
    amount_minor: int,
    currency: str,
    note: str | None,
    recipient: User,
    category_id: int | None,
) -> Transaction:
    tx = Transaction(
        workspace_id=workspace.id,
        wallet_id=wallet.id,
        type=TransactionType.income,
        amount_minor=amount_minor,
        currency=currency,
        note=note,
        created_by=recipient.id,
        category_id=category_id,
    )
    session.add(tx)
    await session.flush()

    session.add(
        TransactionSplit(
            transaction_id=tx.id,
            user_id=recipient.id,
            amount_minor=amount_minor,
        )
    )

    await session.commit()
    await session.refresh(tx)
    return tx
