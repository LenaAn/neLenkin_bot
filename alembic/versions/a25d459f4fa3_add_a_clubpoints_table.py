"""add a ClubPoints table

Revision ID: a25d459f4fa3
Revises: d5605378cae6
Create Date: 2026-07-20 12:53:49.968439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a25d459f4fa3'
down_revision: Union[str, Sequence[str], None] = 'd5605378cae6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ClubPoints',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('balance', sa.Integer(), nullable=False),
    sa.CheckConstraint('balance >= 0', name='ck_club_points_balance_non_negative'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ClubPoints')
