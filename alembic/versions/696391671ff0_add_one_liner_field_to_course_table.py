"""add one-liner field to Course table

Revision ID: 696391671ff0
Revises: 37c65e64c531
Create Date: 2026-02-27 17:04:22.467882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '696391671ff0'
down_revision: Union[str, Sequence[str], None] = '37c65e64c531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Course', sa.Column('one_liner', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Course', 'one_liner')
