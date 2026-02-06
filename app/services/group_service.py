from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditAction, AuditLog, Expense, ExpenseSplit, Group, GroupMember, GroupRole, Settlement, User, Wallet
from app.services.settlement import simplify_settlements


async def ensure_group_member(db: AsyncSession, group_id: int, user_id: int) -> None:
    q = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    if (await db.execute(q)).scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail='Not a group member')


async def create_group(db: AsyncSession, actor: User, name: str, member_ids: list[int]) -> Group:
    group = Group(name=name, created_by=actor.id)
    db.add(group)
    await db.flush()
    unique_members = sorted(set([actor.id, *member_ids]))
    for uid in unique_members:
        role = GroupRole.admin if uid == actor.id else GroupRole.member
        db.add(GroupMember(group_id=group.id, user_id=uid, role=role))
    await db.commit()
    await db.refresh(group)
    return group


async def create_expense(
    db: AsyncSession,
    actor: User,
    group_id: int,
    paid_by: int,
    amount: Decimal,
    currency: str,
    description: str,
    splits: list[tuple[int, Decimal]] | None,
    request_id: str | None,
) -> Expense:
    await ensure_group_member(db, group_id, actor.id)
    await ensure_group_member(db, group_id, paid_by)

    if amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    members_result = await db.execute(select(GroupMember.user_id).where(GroupMember.group_id == group_id))
    member_ids = [m[0] for m in members_result.all()]
    if splits:
        total_owed = sum((s[1] for s in splits), Decimal('0'))
        if total_owed != amount:
            raise HTTPException(status_code=400, detail='Split total must equal expense amount')
        split_data = splits
    else:
        equal = (amount / Decimal(len(member_ids))).quantize(Decimal('0.01'))
        split_data = [(uid, equal) for uid in member_ids]
        diff = amount - sum((s[1] for s in split_data), Decimal('0'))
        split_data[0] = (split_data[0][0], split_data[0][1] + diff)

    expense = Expense(group_id=group_id, paid_by=paid_by, total_amount=amount, currency=currency, description=description)
    db.add(expense)
    await db.flush()

    for uid, owed in split_data:
        db.add(ExpenseSplit(expense_id=expense.id, user_id=uid, amount_owed=owed))

    db.add(AuditLog(actor_user_id=actor.id, action=AuditAction.expense_created, entity_type='expense', entity_id=expense.id, request_id=request_id))
    await db.commit()
    await db.refresh(expense)
    return expense


async def compute_group_balances(db: AsyncSession, group_id: int) -> dict[int, Decimal]:
    paid = await db.execute(
        select(Expense.paid_by, func.coalesce(func.sum(Expense.total_amount), 0))
        .where(Expense.group_id == group_id)
        .group_by(Expense.paid_by)
    )
    owed = await db.execute(
        select(ExpenseSplit.user_id, func.coalesce(func.sum(ExpenseSplit.amount_owed), 0))
        .join(Expense, Expense.id == ExpenseSplit.expense_id)
        .where(Expense.group_id == group_id)
        .group_by(ExpenseSplit.user_id)
    )
    balances: dict[int, Decimal] = {}
    for uid, amt in paid.all():
        balances[uid] = Decimal(amt)
    for uid, amt in owed.all():
        balances[uid] = balances.get(uid, Decimal('0')) - Decimal(amt)
    return balances


async def create_settlements(db: AsyncSession, actor: User, group_id: int, request_id: str | None) -> list[Settlement]:
    await ensure_group_member(db, group_id, actor.id)
    net = await compute_group_balances(db, group_id)
    suggestions = simplify_settlements(net)
    rows: list[Settlement] = []
    for s in suggestions:
        row = Settlement(group_id=group_id, from_user=s['from_user'], to_user=s['to_user'], amount=s['amount'])
        db.add(row)
        await db.flush()
        db.add(AuditLog(actor_user_id=actor.id, action=AuditAction.settlement_executed, entity_type='settlement', entity_id=row.id, request_id=request_id))
        rows.append(row)
    await db.commit()
    return rows


async def transfer_between_wallets(db: AsyncSession, actor: User, to_user_id: int, amount: Decimal, allow_negative: bool, request_id: str | None):
    if amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')
    sender = (await db.execute(select(Wallet).where(Wallet.user_id == actor.id))).scalar_one()
    receiver = (await db.execute(select(Wallet).where(Wallet.user_id == to_user_id))).scalar_one_or_none()
    if receiver is None:
        raise HTTPException(status_code=404, detail='Receiver wallet missing')
    if not allow_negative and sender.balance < amount:
        raise HTTPException(status_code=400, detail='Insufficient balance')

    sender.balance -= amount
    sender.version += 1
    receiver.balance += amount
    receiver.version += 1

    from app.db.models import Transaction
    tx = Transaction(from_wallet=sender.id, to_wallet=receiver.id, amount=amount)
    db.add(tx)
    await db.flush()
    db.add(AuditLog(actor_user_id=actor.id, action=AuditAction.transfer_executed, entity_type='transaction', entity_id=tx.id, request_id=request_id))
    await db.commit()
    return tx
