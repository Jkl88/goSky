"""Статистика переходов, TTL и лимит кликов."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260703_000002"
down_revision: Union[str, None] = "20260703_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("short_links", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("short_links", sa.Column("max_clicks", sa.Integer(), nullable=True))
    op.create_index("ix_short_links_expires_at", "short_links", ["expires_at"], unique=False)

    op.create_table(
        "link_clicks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("device_type", sa.String(length=20), nullable=False),
        sa.Column("clicked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["link_id"], ["short_links.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_link_clicks_clicked_at", "link_clicks", ["clicked_at"], unique=False)
    op.create_index("ix_link_clicks_device_type", "link_clicks", ["device_type"], unique=False)
    op.create_index("ix_link_clicks_ip_address", "link_clicks", ["ip_address"], unique=False)
    op.create_index("ix_link_clicks_link_id", "link_clicks", ["link_id"], unique=False)


def downgrade() -> None:
    op.drop_table("link_clicks")
    op.drop_index("ix_short_links_expires_at", table_name="short_links")
    op.drop_column("short_links", "max_clicks")
    op.drop_column("short_links", "expires_at")
