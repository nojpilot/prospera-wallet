from aiogram import Bot, Dispatcher

from app.handlers import (
    categories_router,
    reports_router,
    start_router,
    transactions_router,
    webapp_router,
    wallets_router,
    workspaces_router,
)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(workspaces_router)
    dp.include_router(wallets_router)
    dp.include_router(categories_router)
    dp.include_router(transactions_router)
    dp.include_router(reports_router)
    dp.include_router(webapp_router)
    return dp


def create_bot(token: str) -> Bot:
    return Bot(token=token)
