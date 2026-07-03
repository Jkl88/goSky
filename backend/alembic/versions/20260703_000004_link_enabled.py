"""add is_enabled to short_links

Revision ID: 20260703_000004
Revises: 20260703_000003
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260703_000004"
down_revision = "20260703_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "short_links",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("short_links", "is_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("short_links", "is_enabled")
