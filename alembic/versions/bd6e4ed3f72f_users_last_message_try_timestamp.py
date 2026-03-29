"""users last message try timestamp

Revision ID: bd6e4ed3f72f
Revises: 33cdee07d65e
Create Date: 2026-03-29 15:11:50.542511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd6e4ed3f72f'
down_revision: Union[str, Sequence[str], None] = '33cdee07d65e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Users', sa.Column('is_last_message_successful', sa.Boolean(), nullable=True))
    op.add_column('Users', sa.Column('last_message_try_time', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Users', 'last_message_try_time')
    op.drop_column('Users', 'is_last_message_successful')
