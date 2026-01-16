"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-02-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

wallet_type_enum = sa.Enum(
    "shared",
    "personal",
    name="wallet_type",
    native_enum=False,
)
transaction_type_enum = sa.Enum(
    "expense",
    "income",
    "transfer",
    name="transaction_type",
    native_enum=False,
)
category_type_enum = sa.Enum(
    "expense",
    "income",
    name="category_type",
    native_enum=False,
)
membership_role_enum = sa.Enum(
    "owner",
    "member",
    name="membership_role",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tg_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "workspaces",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            membership_role_enum,
            nullable=False,
            server_default=sa.text("'member'"),
        ),
        sa.Column(
            "share_weight",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_membership"),
    )

    op.create_table(
        "wallets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", wallet_type_enum, nullable=False),
        sa.Column(
            "owner_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "name", name="uq_wallet_name"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", category_type_enum, nullable=False),
        sa.Column(
            "parent_id",
            sa.BigInteger(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "name", "type", name="uq_category_name"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "wallet_id",
            sa.BigInteger(),
            sa.ForeignKey("wallets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "to_wallet_id",
            sa.BigInteger(),
            sa.ForeignKey("wallets.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            sa.BigInteger(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", transaction_type_enum, nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "transaction_splits",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.BigInteger(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("transaction_id", "user_id", name="uq_transaction_split"),
    )

    op.create_table(
        "fx_rates",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("quote_currency", sa.String(length=3), nullable=False),
        sa.Column("rate_to_base", sa.Numeric(18, 8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "workspace_id", "rate_date", "quote_currency", name="uq_fx_rate"
        ),
    )

    op.create_index("ix_memberships_workspace_id", "memberships", ["workspace_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_wallets_workspace_id", "wallets", ["workspace_id"])
    op.create_index("ix_categories_workspace_id", "categories", ["workspace_id"])
    op.create_index("ix_transactions_workspace_id", "transactions", ["workspace_id"])
    op.create_index("ix_transactions_wallet_id", "transactions", ["wallet_id"])
    op.create_index("ix_transactions_created_by", "transactions", ["created_by"])
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])
    op.create_index(
        "ix_transaction_splits_transaction_id",
        "transaction_splits",
        ["transaction_id"],
    )
    op.create_index("ix_transaction_splits_user_id", "transaction_splits", ["user_id"])
    op.create_index("ix_fx_rates_workspace_id", "fx_rates", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_fx_rates_workspace_id", table_name="fx_rates")
    op.drop_index("ix_transaction_splits_user_id", table_name="transaction_splits")
    op.drop_index(
        "ix_transaction_splits_transaction_id", table_name="transaction_splits"
    )
    op.drop_index("ix_transactions_occurred_at", table_name="transactions")
    op.drop_index("ix_transactions_created_by", table_name="transactions")
    op.drop_index("ix_transactions_wallet_id", table_name="transactions")
    op.drop_index("ix_transactions_workspace_id", table_name="transactions")
    op.drop_index("ix_categories_workspace_id", table_name="categories")
    op.drop_index("ix_wallets_workspace_id", table_name="wallets")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_workspace_id", table_name="memberships")

    op.drop_table("fx_rates")
    op.drop_table("transaction_splits")
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("wallets")
    op.drop_table("memberships")
    op.drop_table("workspaces")
    op.drop_table("users")
