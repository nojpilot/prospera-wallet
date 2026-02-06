from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.models import User, Wallet
from app.db.session import get_db
from app.schemas.api import TransferRequest, WalletResponse
from app.services.group_service import transfer_between_wallets

router = APIRouter(prefix='/wallet', tags=['wallet'])


@router.get('/me', response_model=WalletResponse)
async def wallet_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))).scalar_one()
    return WalletResponse(id=wallet.id, balance=wallet.balance, currency=wallet.currency)


@router.post('/transfer')
async def transfer(payload: TransferRequest, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    tx = await transfer_between_wallets(db, current_user, payload.to_user_id, payload.amount, settings.allow_negative_balances, request.state.request_id)
    return {'id': tx.id, 'status': tx.status}
