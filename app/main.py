import logging

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import InMemoryRateLimitMiddleware, RequestContextMiddleware

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title='Prospera Wallet API', version='1.0.0')
app.add_middleware(RequestContextMiddleware)
app.add_middleware(InMemoryRateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)


@app.get('/health')
async def health():
    return {'status': 'ok'}
