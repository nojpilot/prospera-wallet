from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Transaction, TransactionType, Workspace
from app.services.utils import format_minor


def _month_range(now: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


async def monthly_expense_report(
    session: AsyncSession,
    workspace: Workspace,
    now: dt.datetime | None = None,
) -> str:
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    start, end = _month_range(now)

    category_label = func.coalesce(Category.name, "Uncategorized")

    stmt = (
        select(
            category_label.label("category"),
            Transaction.currency.label("currency"),
            func.sum(Transaction.amount_minor).label("total_minor"),
        )
        .select_from(Transaction)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.workspace_id == workspace.id,
            Transaction.type == TransactionType.expense,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(category_label, Transaction.currency)
        .order_by(Transaction.currency, func.sum(Transaction.amount_minor).desc())
    )

    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        return "No expenses for this month yet."

    lines: list[str] = []
    current_currency = None
    for category, currency, total_minor in rows:
        if currency != current_currency:
            current_currency = currency
            lines.append(f"{currency}:")
        lines.append(f"- {category}: {format_minor(int(total_minor), currency)}")
    return "\n".join(lines)
