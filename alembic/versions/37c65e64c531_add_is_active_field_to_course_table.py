"""add is_active field to Course table

Revision ID: 37c65e64c531
Revises: aee84c09342f
Create Date: 2026-02-27 16:39:43.297320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37c65e64c531'
down_revision: Union[str, Sequence[str], None] = 'aee84c09342f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('is_active', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Course', 'is_active')
