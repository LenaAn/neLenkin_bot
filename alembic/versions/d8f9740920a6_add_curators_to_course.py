"""add curators to course

Revision ID: d8f9740920a6
Revises: 2d40f6e36eb3
Create Date: 2025-08-07 16:55:40.172847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f9740920a6'
down_revision: Union[str, Sequence[str], None] = '2d40f6e36eb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('curator_tg_id', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Course', 'curator_tg_id')
