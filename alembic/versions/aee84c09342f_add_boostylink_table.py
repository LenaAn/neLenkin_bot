"""add BoostyLink table

Revision ID: aee84c09342f
Revises: a627e2bff2dc
Create Date: 2026-02-03 15:45:11.899723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aee84c09342f'
down_revision: Union[str, Sequence[str], None] = 'a627e2bff2dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('BoostyLink',
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('tg_username', sa.Text(), nullable=True),
    sa.Column('boosty_user_id', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['tg_id'], ['Users.tg_id'], name='fk_valid_tg_id'),
    sa.PrimaryKeyConstraint('tg_id'),
    sa.UniqueConstraint('boosty_user_id', name='Boosty_user_id_is_unique')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('BoostyLink')
