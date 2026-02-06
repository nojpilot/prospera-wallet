from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.models import User, Wallet
from app.db.session import get_db
from app.webapp_auth import WebAppAuthError, extract_user, validate_init_data
from app.core.config import get_settings

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/telegram-miniapp')
async def telegram_miniapp_auth(x_telegram_init_data: str = Header(default=''), db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    try:
        data = validate_init_data(x_telegram_init_data, settings.bot_token)
        tg_user = extract_user(data)
    except WebAppAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    telegram_id = int(tg_user['id'])
    user = (await db.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
    if not user:
        user = User(telegram_id=telegram_id, username=tg_user.get('username'))
        db.add(user)
        await db.flush()
        db.add(Wallet(user_id=user.id, balance=0, currency='USD'))
        await db.commit()
    return {'access_token': create_access_token(str(user.id)), 'token_type': 'bearer'}
