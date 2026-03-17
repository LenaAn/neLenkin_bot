"""add is_pro field to the Course table

Revision ID: 33cdee07d65e
Revises: 47dcc2406c3b
Create Date: 2026-03-17 18:16:51.692250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33cdee07d65e'
down_revision: Union[str, Sequence[str], None] = '47dcc2406c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('is_pro', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Course', 'is_pro')
