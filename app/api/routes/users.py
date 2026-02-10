from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models import User
from app.db.session import get_db
from app.schemas.api import AuthResponse, RegisterUserRequest

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/register', response_model=AuthResponse)
async def register(payload: RegisterUserRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.tg_id == payload.telegram_id))).scalar_one_or_none()
    if existing:
        token = create_access_token(str(existing.id))
        return AuthResponse(access_token=token)

    user = User(tg_id=payload.telegram_id, username=payload.username)
    db.add(user)
    await db.commit()
    token = create_access_token(str(user.id))
    return AuthResponse(access_token=token)
