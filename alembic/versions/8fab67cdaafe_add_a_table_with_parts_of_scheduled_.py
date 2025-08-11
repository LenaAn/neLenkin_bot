"""add a table with parts of scheduled messages

Revision ID: 8fab67cdaafe
Revises: d8f9740920a6
Create Date: 2025-08-11 11:50:56.961145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fab67cdaafe'
down_revision: Union[str, Sequence[str], None] = 'd8f9740920a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ScheduledPartMessages',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('week_number', 'course_id', name='Unique_message_per_week_and_course')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ScheduledPartMessages')
