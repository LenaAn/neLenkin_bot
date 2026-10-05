"""add a table for random coffee sign up

Revision ID: 910618a104d6
Revises: 47ccc3189882
Create Date: 2026-10-05 20:36:51.921045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '910618a104d6'
down_revision: Union[str, Sequence[str], None] = '47ccc3189882'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('RandomCoffeeSignUp',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('week_number', 'tg_id', 'year', name='random_coffee_one_record_per_user_per_week')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('RandomCoffeeSignUp')
