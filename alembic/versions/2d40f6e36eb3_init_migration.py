"""init migration

Revision ID: 2d40f6e36eb3
Revises: 
Create Date: 2025-08-01 14:52:54.770723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d40f6e36eb3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Course',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('date_start', sa.Date(), nullable=True),
    sa.Column('date_end', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Enrollments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.Column('course_id', sa.BigInteger(), nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_id', 'course_id', name='Unique_tg_id_per_course')
    )
    op.create_table('Users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('tg_username', sa.Text(), nullable=True),
    sa.Column('first_name', sa.Text(), nullable=True),
    sa.Column('last_name', sa.Text(), nullable=True),
    sa.Column('date_joined', sa.JSON(), nullable=True),
    sa.Column('date_membership_started', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('Users')
    op.drop_table('Enrollments')
    op.drop_table('Course')
