from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, CategoryType, Workspace


async def list_categories(
    session: AsyncSession,
    workspace: Workspace,
    category_type: str | None = None,
) -> list[Category]:
    stmt = select(Category).where(Category.workspace_id == workspace.id)
    if category_type:
        stmt = stmt.where(Category.type == CategoryType(category_type))
    result = await session.execute(stmt.order_by(Category.name))
    return list(result.scalars().all())


async def get_category_by_name(
    session: AsyncSession,
    workspace: Workspace,
    name: str,
    category_type: str,
) -> Category | None:
    result = await session.execute(
        select(Category).where(
            Category.workspace_id == workspace.id,
            Category.type == CategoryType(category_type),
            func.lower(Category.name) == name.lower(),
        )
    )
    return result.scalar_one_or_none()


async def get_or_create_category(
    session: AsyncSession,
    workspace: Workspace,
    name: str,
    category_type: str,
) -> Category:
    category = await get_category_by_name(session, workspace, name, category_type)
    if category:
        return category
    category = Category(
        workspace_id=workspace.id,
        name=name,
        type=CategoryType(category_type),
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def ensure_default_categories(session: AsyncSession, workspace: Workspace) -> None:
    defaults = [
        ("Other", "expense"),
        ("Other", "income"),
    ]
    created = False
    for name, category_type in defaults:
        existing = await get_category_by_name(session, workspace, name, category_type)
        if existing is None:
            session.add(
                Category(
                    workspace_id=workspace.id,
                    name=name,
                type=CategoryType(category_type),
                )
            )
            created = True
    if created:
        await session.commit()
