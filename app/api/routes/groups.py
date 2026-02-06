from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models import Group, GroupMember, User
from app.db.session import get_db
from app.schemas.api import CreateExpenseRequest, CreateGroupRequest, GroupResponse
from app.services.group_service import compute_group_balances, create_expense, create_group, create_settlements, ensure_group_member

router = APIRouter(prefix='/groups', tags=['groups'])


@router.post('', response_model=GroupResponse)
async def create_group_endpoint(payload: CreateGroupRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    group = await create_group(db, current_user, payload.name, payload.member_ids)
    return GroupResponse(id=group.id, name=group.name, created_by=group.created_by)


@router.get('/{group_id}')
async def get_group(group_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await ensure_group_member(db, group_id, current_user.id)
    group = (await db.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail='Group not found')
    members = (await db.execute(select(GroupMember.user_id, GroupMember.role).where(GroupMember.group_id == group_id))).all()
    return {'id': group.id, 'name': group.name, 'created_by': group.created_by, 'members': [{'user_id': m[0], 'role': m[1].value} for m in members]}


@router.post('/{group_id}/expenses')
async def add_expense(group_id: int, payload: CreateExpenseRequest, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    splits = None if payload.splits is None else [(s.user_id, s.amount_owed) for s in payload.splits]
    expense = await create_expense(db, current_user, group_id, payload.paid_by, payload.total_amount, payload.currency, payload.description, splits, request.state.request_id)
    return {'id': expense.id}


@router.get('/{group_id}/balances')
async def balances(group_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await ensure_group_member(db, group_id, current_user.id)
    bal = await compute_group_balances(db, group_id)
    return {'group_id': group_id, 'balances': {str(k): str(v) for k, v in bal.items()}}


@router.post('/{group_id}/settlements')
async def settle(group_id: int, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await create_settlements(db, current_user, group_id, request.state.request_id)
    return {'group_id': group_id, 'settlements': [{'from_user': r.from_user, 'to_user': r.to_user, 'amount': str(r.amount), 'status': r.status.value} for r in rows]}
