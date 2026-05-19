"""get rid of hour and day_of_week in course

Revision ID: 0b01970a6e54
Revises: 070a62f5bd23
Create Date: 2026-05-19 15:47:44.821661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b01970a6e54'
down_revision: Union[str, Sequence[str], None] = '070a62f5bd23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        constraint_name="check_day_of_week_range",
        table_name="Course",
        type_="check"
    )
    op.drop_constraint(
        constraint_name="check_hour_of_day_range",
        table_name="Course",
        type_="check"
    )
    op.drop_column('Course', 'hour')
    op.drop_column('Course', 'day_of_week')


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column('Course', sa.Column('day_of_week', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('Course', sa.Column('hour', sa.INTEGER(), autoincrement=False, nullable=True))

    op.create_check_constraint(
        constraint_name="check_hour_of_day_range",
        table_name="Course",
        condition="hour BETWEEN 0 AND 23"
    )
    op.create_check_constraint(
        constraint_name="check_day_of_week_range",
        table_name="Course",
        condition="day_of_week BETWEEN 0 AND 6"
    )
