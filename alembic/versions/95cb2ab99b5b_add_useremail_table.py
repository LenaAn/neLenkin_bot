"""add UserEmail table

Revision ID: 95cb2ab99b5b
Revises: bd6e4ed3f72f
Create Date: 2026-04-06 18:48:30.601041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95cb2ab99b5b'
down_revision: Union[str, Sequence[str], None] = 'bd6e4ed3f72f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('UserEmail',
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('contact_email', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['tg_id'], ['Users.tg_id'], name='fk_valid_tg_id'),
    sa.PrimaryKeyConstraint('tg_id'),
    sa.UniqueConstraint('contact_email', name='User_contact_email_is_unique')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('UserEmail')
