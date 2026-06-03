"""add a discussion thread id to the Course

Revision ID: d5605378cae6
Revises: 0b01970a6e54
Create Date: 2026-06-03 16:37:42.656287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5605378cae6'
down_revision: Union[str, Sequence[str], None] = '0b01970a6e54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('discussion_thread_id', sa.Integer(), nullable=True))
    op.create_unique_constraint('unique_discussion_thread_id', 'Course', ['discussion_thread_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('unique_discussion_thread_id', 'Course', type_='unique')
    op.drop_column('Course', 'discussion_thread_id')
