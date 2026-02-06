from decimal import Decimal

from pydantic import BaseModel, Field


class RegisterUserRequest(BaseModel):
    telegram_id: int
    username: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class WalletResponse(BaseModel):
    id: int
    balance: Decimal
    currency: str


class CreateGroupRequest(BaseModel):
    name: str
    member_ids: list[int] = Field(default_factory=list)


class GroupResponse(BaseModel):
    id: int
    name: str
    created_by: int


class ExpenseSplitInput(BaseModel):
    user_id: int
    amount_owed: Decimal


class CreateExpenseRequest(BaseModel):
    paid_by: int
    total_amount: Decimal
    currency: str
    description: str
    splits: list[ExpenseSplitInput] | None = None


class SettlementSuggestion(BaseModel):
    from_user: int
    to_user: int
    amount: Decimal


class TransferRequest(BaseModel):
    to_user_id: int
    amount: Decimal
