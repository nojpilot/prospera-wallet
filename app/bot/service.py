from __future__ import annotations

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from fastapi import FastAPI, Header, HTTPException, Request
import httpx

from app.core.config import get_settings

settings = get_settings()
bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


class ExpenseFlow(StatesGroup):
    group_id = State()
    amount = State()
    description = State()


@router.message(Command('start'))
async def start_cmd(message: Message):
    async with httpx.AsyncClient() as client:
        await client.post('http://api:8000/api/v1/users/register', json={'telegram_id': message.from_user.id, 'username': message.from_user.username})
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Create Group', callback_data='newgroup')]])
    await message.answer('Welcome to Prospera wallet bot.', reply_markup=kb)


@router.message(Command('balance'))
async def balance_cmd(message: Message):
    await message.answer('Use Mini App/API token for secure balance view.')


@router.message(Command('groups'))
async def groups_cmd(message: Message):
    await message.answer('Use /newgroup to create one or Mini App to list all groups.')


@router.message(Command('newgroup'))
async def newgroup_cmd(message: Message):
    await message.answer('Create groups from Mini App for secure member selection.')


@router.message(Command('addexpense'))
async def addexpense_start(message: Message, state: FSMContext):
    await state.set_state(ExpenseFlow.group_id)
    await message.answer('Enter group id')


@router.message(ExpenseFlow.group_id)
async def addexpense_group(message: Message, state: FSMContext):
    await state.update_data(group_id=int(message.text))
    await state.set_state(ExpenseFlow.amount)
    await message.answer('Enter amount')


@router.message(ExpenseFlow.amount)
async def addexpense_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(ExpenseFlow.description)
    await message.answer('Enter description')


@router.message(ExpenseFlow.description)
async def addexpense_done(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await message.answer(f"Expense draft saved for group {data['group_id']}: {data['amount']} {message.text}")


@router.message(Command('groupbalance'))
async def groupbalance_cmd(message: Message):
    await message.answer('Use Mini App for rich group balances.')


@router.message(Command('settle'))
async def settle_cmd(message: Message):
    await message.answer('Use Mini App to review deterministic settlement suggestions.')


dp.include_router(router)
app = FastAPI(title='Prospera Telegram Bot')


@app.post(settings.bot_webhook_path)
async def telegram_webhook(update: dict, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if x_telegram_bot_api_secret_token != settings.bot_webhook_secret:
        raise HTTPException(status_code=401, detail='Invalid webhook secret')
    await dp.feed_update(bot, Update.model_validate(update))
    return {'ok': True}


@app.on_event('startup')
async def startup_event():
    webhook_url = f"http://localhost:8001{settings.bot_webhook_path}"
    await bot.set_webhook(webhook_url, secret_token=settings.bot_webhook_secret)


@app.on_event('shutdown')
async def shutdown_event():
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
