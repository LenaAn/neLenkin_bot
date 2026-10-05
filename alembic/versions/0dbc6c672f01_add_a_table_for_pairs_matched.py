"""add a table for pairs matched

Revision ID: 0dbc6c672f01
Revises: 910618a104d6
Create Date: 2026-10-05 20:38:29.531428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dbc6c672f01'
down_revision: Union[str, Sequence[str], None] = '910618a104d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('PairsMatched',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('course_id', sa.BigInteger(), nullable=False),
    sa.Column('first_tg_id', sa.Text(), nullable=False),
    sa.Column('second_tg_id', sa.Text(), nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('PairsMatched')
