from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Wallet, Workspace


async def list_wallets(session: AsyncSession, workspace: Workspace) -> list[Wallet]:
    result = await session.execute(
        select(Wallet)
        .where(Wallet.workspace_id == workspace.id)
        .order_by(Wallet.type, Wallet.name)
    )
    return list(result.scalars().all())


async def get_wallet_by_name(
    session: AsyncSession,
    workspace: Workspace,
    name: str,
) -> Wallet | None:
    result = await session.execute(
        select(Wallet).where(
            Wallet.workspace_id == workspace.id,
            func.lower(Wallet.name) == name.lower(),
        )
    )
    return result.scalar_one_or_none()


async def get_shared_wallet(
    session: AsyncSession,
    workspace: Workspace,
    currency: str | None = None,
) -> Wallet | None:
    stmt = select(Wallet).where(
        Wallet.workspace_id == workspace.id,
        Wallet.type == "shared",
        Wallet.is_active.is_(True),
    )
    if currency:
        stmt = stmt.where(Wallet.currency == currency)
    result = await session.execute(stmt.order_by(Wallet.id))
    return result.scalars().first()


async def get_personal_wallet(
    session: AsyncSession,
    workspace: Workspace,
    user: User,
    currency: str | None = None,
) -> Wallet | None:
    stmt = select(Wallet).where(
        Wallet.workspace_id == workspace.id,
        Wallet.type == "personal",
        Wallet.owner_user_id == user.id,
        Wallet.is_active.is_(True),
    )
    if currency:
        stmt = stmt.where(Wallet.currency == currency)
    result = await session.execute(stmt.order_by(Wallet.id))
    return result.scalars().first()


async def create_wallet(
    session: AsyncSession,
    workspace: Workspace,
    name: str,
    wallet_type: str,
    currency: str,
    owner_user_id: int | None = None,
) -> Wallet:
    wallet = Wallet(
        workspace_id=workspace.id,
        name=name,
        type=wallet_type,
        owner_user_id=owner_user_id,
        currency=currency,
    )
    session.add(wallet)
    await session.commit()
    await session.refresh(wallet)
    return wallet


async def ensure_default_wallets(
    session: AsyncSession,
    workspace: Workspace,
    owner: User,
) -> list[Wallet]:
    wallets: list[Wallet] = []
    shared = await get_shared_wallet(session, workspace, workspace.base_currency)
    if shared is None:
        shared = Wallet(
            workspace_id=workspace.id,
            name="Shared",
            type="shared",
            currency=workspace.base_currency,
        )
        session.add(shared)
        wallets.append(shared)

    personal = await get_personal_wallet(
        session, workspace, owner, workspace.base_currency
    )
    if personal is None:
        label = owner.first_name or owner.username or str(owner.tg_id)
        personal = Wallet(
            workspace_id=workspace.id,
            name=f"Personal {label}",
            type="personal",
            owner_user_id=owner.id,
            currency=workspace.base_currency,
        )
        session.add(personal)
        wallets.append(personal)

    if wallets:
        await session.commit()
        for wallet in wallets:
            await session.refresh(wallet)
    return wallets


async def get_default_wallet(
    session: AsyncSession,
    workspace: Workspace,
    user: User,
    currency: str,
) -> Wallet | None:
    shared = await get_shared_wallet(session, workspace, currency)
    if shared:
        return shared
    personal = await get_personal_wallet(session, workspace, user, currency)
    if personal:
        return personal
    return None
