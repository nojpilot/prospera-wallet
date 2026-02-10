from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import User
from app.services.balance import calculate_balances
from app.services.categories import ensure_default_categories, get_or_create_category
from app.services.reporting import monthly_expense_report
from app.services.transactions import create_expense
from app.services.wallets import ensure_default_wallets, get_default_wallet
from app.services.workspaces import add_member, create_workspace


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_workspace_balances(session_factory):
    async with session_factory() as session:
        u1 = User(tg_id=1, first_name="A")
        u2 = User(tg_id=2, first_name="B")
        session.add_all([u1, u2])
        await session.commit()
        await session.refresh(u1)
        await session.refresh(u2)

        workspace = await create_workspace(session, u1, "Trip", "USD")
        await add_member(session, workspace, u2)
        await ensure_default_wallets(session, workspace, u1)
        await ensure_default_categories(session, workspace)

        wallet = await get_default_wallet(session, workspace, u1, "USD")
        assert wallet is not None
        category = await get_or_create_category(session, workspace, "Other", "expense")

        await create_expense(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=1000,
            currency="USD",
            note="Lunch",
            payer=u1,
            category_id=category.id,
        )

        balances = await calculate_balances(session, workspace)
        assert balances["USD"][u1.id] == 500
        assert balances["USD"][u2.id] == -500


@pytest.mark.asyncio
async def test_monthly_report(session_factory):
    async with session_factory() as session:
        u1 = User(tg_id=10, first_name="A")
        session.add(u1)
        await session.commit()
        await session.refresh(u1)

        workspace = await create_workspace(session, u1, "Budget", "USD")
        await ensure_default_wallets(session, workspace, u1)
        await ensure_default_categories(session, workspace)

        wallet = await get_default_wallet(session, workspace, u1, "USD")
        assert wallet is not None
        category = await get_or_create_category(session, workspace, "Other", "expense")

        await create_expense(
            session,
            workspace=workspace,
            wallet=wallet,
            amount_minor=2500,
            currency="USD",
            note="Cafe",
            payer=u1,
            category_id=category.id,
        )

        report = await monthly_expense_report(session, workspace, now=dt.datetime.now(dt.timezone.utc))
        assert "USD" in report
        assert "Other" in report
