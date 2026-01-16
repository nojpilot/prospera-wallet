from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


wallet_type_enum = Enum(
    "shared",
    "personal",
    name="wallet_type",
    native_enum=False,
)
transaction_type_enum = Enum(
    "expense",
    "income",
    "transfer",
    name="transaction_type",
    native_enum=False,
)
category_type_enum = Enum(
    "expense",
    "income",
    name="category_type",
    native_enum=False,
)
membership_role_enum = Enum(
    "owner",
    "member",
    name="membership_role",
    native_enum=False,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    active_workspace_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    active_workspace: Mapped[Workspace | None] = relationship(
        "Workspace", foreign_keys=[active_workspace_id]
    )
    memberships: Mapped[list[Membership]] = relationship("Membership", back_populates="user")
    created_transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="creator"
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    memberships: Mapped[list[Membership]] = relationship(
        "Membership", back_populates="workspace"
    )
    wallets: Mapped[list[Wallet]] = relationship("Wallet", back_populates="workspace")
    categories: Mapped[list[Category]] = relationship(
        "Category", back_populates="workspace"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="workspace"
    )


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_membership"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(
        membership_role_enum, nullable=False, server_default=text("'member'")
    )
    share_weight: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="memberships")
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="memberships")


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_wallet_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(wallet_type_enum, nullable=False)
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="wallets")
    owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_user_id])


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", "type", name="uq_category_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(category_type_enum, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="categories")
    parent: Mapped[Category | None] = relationship("Category", remote_side="Category.id")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    wallet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wallets.id", ondelete="RESTRICT"), index=True
    )
    to_wallet_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("wallets.id", ondelete="RESTRICT")
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL")
    )
    type: Mapped[str] = mapped_column(transaction_type_enum, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="transactions")
    wallet: Mapped[Wallet] = relationship("Wallet", foreign_keys=[wallet_id])
    to_wallet: Mapped[Wallet | None] = relationship("Wallet", foreign_keys=[to_wallet_id])
    category: Mapped[Category | None] = relationship("Category")
    creator: Mapped[User | None] = relationship("User", back_populates="created_transactions")
    splits: Mapped[list[TransactionSplit]] = relationship(
        "TransactionSplit", back_populates="transaction"
    )


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"
    __table_args__ = (
        UniqueConstraint("transaction_id", "user_id", name="uq_transaction_split"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("transactions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction: Mapped[Transaction] = relationship("Transaction", back_populates="splits")
    user: Mapped[User] = relationship("User")


class FxRate(Base):
    __tablename__ = "fx_rates"
    __table_args__ = (
        UniqueConstraint("workspace_id", "rate_date", "quote_currency", name="uq_fx_rate"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    rate_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_to_base: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped[Workspace] = relationship("Workspace")
