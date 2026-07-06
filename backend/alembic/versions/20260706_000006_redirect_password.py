"""add redirect_password_hash to short_links

Revision ID: 20260706_000006
Revises: 20260705_000005
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260706_000006"
down_revision = "20260705_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("short_links", sa.Column("redirect_password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("short_links", "redirect_password_hash")
