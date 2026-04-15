"""add day of the week to courses

Revision ID: 4d24102547b1
Revises: 95cb2ab99b5b
Create Date: 2026-04-15 12:44:32.965199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d24102547b1'
down_revision: Union[str, Sequence[str], None] = '95cb2ab99b5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('day_of_week', sa.Integer(), nullable=True))
    op.create_check_constraint(
        constraint_name="check_day_of_week_range",
        table_name="Course",
        condition="day_of_week BETWEEN 0 AND 6"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        constraint_name="check_day_of_week_range",
        table_name="Course",
        type_="check"
    )
    op.drop_column('Course', 'day_of_week')
