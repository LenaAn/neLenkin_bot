"""add table for mocks sign-ups

Revision ID: 88655167d4e7
Revises: 8fab67cdaafe
Create Date: 2025-08-15 13:36:00.965086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88655167d4e7'
down_revision: Union[str, Sequence[str], None] = '8fab67cdaafe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('MockSignUp',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('tg_username', sa.Text(), nullable=True),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('first_problem', sa.Text(), nullable=False),
    sa.Column('second_problem', sa.Text(), nullable=False),
    sa.Column('selected_timeslots', sa.JSON(), nullable=False),
    sa.Column('programming_language', sa.Text(), nullable=False),
    sa.Column('english_choice', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('week_number', 'tg_id', name='One_record_per_user_per_week')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('MockSignUp')
