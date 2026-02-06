from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import User
from app.services.group_service import compute_group_balances, create_expense, create_group, create_settlements, ensure_group_member


@pytest.fixture
async def session_factory():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_group_balances_and_settlement(session_factory):
    async with session_factory() as session:
        u1 = User(telegram_id=1, username='u1')
        u2 = User(telegram_id=2, username='u2')
        session.add_all([u1, u2])
        await session.commit()
        await session.refresh(u1)
        await session.refresh(u2)

        group = await create_group(session, u1, 'trip', [u2.id])
        await create_expense(session, u1, group.id, u1.id, Decimal('20.00'), 'USD', 'Lunch', None, 'req-1')
        balances = await compute_group_balances(session, group.id)
        assert balances[u1.id] == Decimal('10.00')
        assert balances[u2.id] == Decimal('-10.00')

        settlements = await create_settlements(session, u1, group.id, 'req-2')
        assert len(settlements) == 1
        assert settlements[0].from_user == u2.id


@pytest.mark.asyncio
async def test_permission_violation(session_factory):
    async with session_factory() as session:
        owner = User(telegram_id=10, username='owner')
        outsider = User(telegram_id=11, username='outsider')
        session.add_all([owner, outsider])
        await session.commit()
        await session.refresh(owner)
        await session.refresh(outsider)
        group = await create_group(session, owner, 'g', [])
        with pytest.raises(HTTPException):
            await ensure_group_member(session, group.id, outsider.id)


@pytest.mark.asyncio
async def test_repeated_settlement_requests_are_deterministic(session_factory):
    async with session_factory() as session:
        u1 = User(telegram_id=21, username='u1')
        u2 = User(telegram_id=22, username='u2')
        u3 = User(telegram_id=23, username='u3')
        session.add_all([u1, u2, u3])
        await session.commit()
        for u in (u1, u2, u3):
            await session.refresh(u)

        group = await create_group(session, u1, 'team', [u2.id, u3.id])
        await create_expense(session, u1, group.id, u1.id, Decimal('30.00'), 'USD', 'Taxi', None, 'req-3')

        r1 = await create_settlements(session, u1, group.id, 'req-4')
        r2 = await create_settlements(session, u1, group.id, 'req-5')
        assert [(x.from_user, x.to_user, x.amount) for x in r1] == [(x.from_user, x.to_user, x.amount) for x in r2]
