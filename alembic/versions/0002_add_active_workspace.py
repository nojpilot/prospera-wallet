"""add active workspace to users

Revision ID: 0002_add_active_workspace
Revises: 0001_initial
Create Date: 2025-02-14 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_active_workspace"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "active_workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_users_active_workspace_id", "users", ["active_workspace_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_users_active_workspace_id", table_name="users")
    op.drop_column("users", "active_workspace_id")
