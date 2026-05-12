"""add hour of meeting to Course db

Revision ID: 6e46b4ba237c
Revises: 3228656f462e
Create Date: 2026-05-12 18:07:46.203661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e46b4ba237c'
down_revision: Union[str, Sequence[str], None] = '3228656f462e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('hour', sa.Integer(), nullable=True))
    op.create_check_constraint(
        constraint_name="check_hour_of_day_range",
        table_name="Course",
        condition="hour BETWEEN 0 AND 23"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        constraint_name="check_hour_of_day_range",
        table_name="Course",
        type_="check"
    )
    op.drop_column('Course', 'hour')
