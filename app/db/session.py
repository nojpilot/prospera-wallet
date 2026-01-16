from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_database_url


engine = create_async_engine(get_database_url(), pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
