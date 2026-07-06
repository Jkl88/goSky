"""slug column up to 12 chars for custom codes

Revision ID: 20260705_000005
Revises: 20260703_000004
Create Date: 2026-07-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_000005"
down_revision: Union[str, None] = "20260703_000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "short_links",
        "slug",
        existing_type=sa.String(length=6),
        type_=sa.String(length=12),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "short_links",
        "slug",
        existing_type=sa.String(length=12),
        type_=sa.String(length=6),
        existing_nullable=False,
    )
