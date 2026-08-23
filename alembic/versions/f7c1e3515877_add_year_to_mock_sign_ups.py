"""add year to mock sign ups

Revision ID: f7c1e3515877
Revises: a25d459f4fa3
Create Date: 2026-08-23 23:50:50.440933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7c1e3515877'
down_revision: Union[str, Sequence[str], None] = 'a25d459f4fa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('MockSignUp', sa.Column('year', sa.Integer(), nullable=True))
    op.drop_constraint(op.f('One_record_per_user_per_week'), 'MockSignUp', type_='unique')
    op.create_unique_constraint('One_record_per_user_per_week', 'MockSignUp', ['week_number', 'tg_id', 'year'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('One_record_per_user_per_week', 'MockSignUp', type_='unique')
    op.create_unique_constraint(op.f('One_record_per_user_per_week'), 'MockSignUp', ['week_number', 'tg_id'],
                                postgresql_nulls_not_distinct=False)
    op.drop_column('MockSignUp', 'year')
