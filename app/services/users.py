from __future__ import annotations

from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def ensure_user(session: AsyncSession, tg_user: TgUser) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user:
        updated = False
        if user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            updated = True
        if user.last_name != tg_user.last_name:
            user.last_name = tg_user.last_name
            updated = True
        if user.username != tg_user.username:
            user.username = tg_user.username
            updated = True
        if updated:
            await session.commit()
        return user

    user = User(
        tg_id=tg_user.id,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        username=tg_user.username,
    )
    session.add(user)
    await session.commit()
    return user


async def ensure_user_from_payload(session: AsyncSession, payload: dict) -> User:
    tg_id_raw = payload.get("id")
    if tg_id_raw is None:
        raise ValueError("Missing Telegram user id")
    tg_id = int(tg_id_raw)

    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    username = payload.get("username")

    if user:
        updated = False
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if user.username != username:
            user.username = username
            updated = True
        if updated:
            await session.commit()
        return user

    user = User(
        tg_id=tg_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
    )
    session.add(user)
    await session.commit()
    return user
