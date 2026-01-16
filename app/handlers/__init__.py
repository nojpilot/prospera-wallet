from app.handlers.categories import router as categories_router
from app.handlers.reports import router as reports_router
from app.handlers.start import router as start_router
from app.handlers.transactions import router as transactions_router
from app.handlers.webapp import router as webapp_router
from app.handlers.wallets import router as wallets_router
from app.handlers.workspaces import router as workspaces_router

__all__ = [
    "categories_router",
    "reports_router",
    "start_router",
    "transactions_router",
    "webapp_router",
    "wallets_router",
    "workspaces_router",
]
