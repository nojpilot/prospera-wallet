from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Membership, MembershipRole, User, Workspace


async def create_workspace(
    session: AsyncSession,
    owner: User,
    name: str,
    base_currency: str,
) -> Workspace:
    workspace = Workspace(name=name, base_currency=base_currency.upper())
    session.add(workspace)
    await session.flush()

    membership = Membership(
        workspace_id=workspace.id,
        user_id=owner.id,
        role=MembershipRole.owner,
        share_weight=1,
    )
    session.add(membership)
    owner.active_workspace_id = workspace.id
    await session.commit()
    await session.refresh(workspace)
    return workspace


async def get_workspace_by_id(
    session: AsyncSession,
    workspace_id: int,
) -> Workspace | None:
    result = await session.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    return result.scalar_one_or_none()


async def add_member(
    session: AsyncSession,
    workspace: Workspace,
    user: User,
) -> Membership:
    result = await session.execute(
        select(Membership).where(
            Membership.workspace_id == workspace.id,
            Membership.user_id == user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership:
        return membership

    membership = Membership(
        workspace_id=workspace.id,
        user_id=user.id,
        role=MembershipRole.member,
    )
    session.add(membership)
    user.active_workspace_id = workspace.id
    await session.commit()
    return membership


async def list_user_workspaces(
    session: AsyncSession,
    user: User,
) -> list[Workspace]:
    result = await session.execute(
        select(Workspace)
        .join(Membership, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == user.id)
        .order_by(Workspace.id)
    )
    return list(result.scalars().all())


async def set_active_workspace(
    session: AsyncSession,
    user: User,
    workspace_id: int | None,
) -> None:
    user.active_workspace_id = workspace_id
    await session.commit()


async def get_active_workspace(
    session: AsyncSession,
    user: User,
) -> Workspace | None:
    if user.active_workspace_id is None:
        return None

    result = await session.execute(
        select(Workspace).where(Workspace.id == user.active_workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        return None

    membership_result = await session.execute(
        select(Membership).where(
            Membership.workspace_id == workspace.id,
            Membership.user_id == user.id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if membership is None:
        return None
    return workspace
