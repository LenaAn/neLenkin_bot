"""make is_active required for Course model

Revision ID: 47dcc2406c3b
Revises: 696391671ff0
Create Date: 2026-02-27 19:42:44.287246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47dcc2406c3b'
down_revision: Union[str, Sequence[str], None] = '696391671ff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Course', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Course', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)
