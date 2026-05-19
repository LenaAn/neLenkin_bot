"""separate table for course notifications

Revision ID: 070a62f5bd23
Revises: 6e46b4ba237c
Create Date: 2026-05-19 13:34:19.799276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '070a62f5bd23'
down_revision: Union[str, Sequence[str], None] = '6e46b4ba237c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('CourseNotification',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('is_zoom_link_only_to_pro', sa.Boolean(), nullable=False),
    sa.Column('send_patreon_reminder', sa.Boolean(), nullable=False),
    sa.Column('day_of_week', sa.Integer(), nullable=False),
    sa.Column('hour', sa.Integer(), nullable=False),
    sa.CheckConstraint('day_of_week BETWEEN 0 AND 6', name='check_day_of_week_range'),
    sa.CheckConstraint('hour BETWEEN 0 AND 23', name='check_hour_of_day_range'),
    sa.ForeignKeyConstraint(['course_id'], ['Course.id'], name='fk_valid_course_id'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id', name='Single_notification_per_course')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('CourseNotification')
