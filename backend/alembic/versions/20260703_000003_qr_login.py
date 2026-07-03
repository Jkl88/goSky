"""Миграция: QR-вход."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260703_000003"
down_revision: Union[str, None] = "20260703_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "qr_login_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_qr_login_links_expires_at", "qr_login_links", ["expires_at"], unique=False)
    op.create_index("ix_qr_login_links_user_id", "qr_login_links", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("qr_login_links")
