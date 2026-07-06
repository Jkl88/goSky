"""add hide_target_url to short_links

Revision ID: 20260706_000007
Revises: 20260706_000006
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260706_000007"
down_revision = "20260706_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "short_links",
        sa.Column("hide_target_url", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("short_links", "hide_target_url", server_default=None)


def downgrade() -> None:
    op.drop_column("short_links", "hide_target_url")
