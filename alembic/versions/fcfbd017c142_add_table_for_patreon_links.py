"""add table for patreon links

Revision ID: fcfbd017c142
Revises: 88655167d4e7
Create Date: 2025-10-15 20:18:49.947151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcfbd017c142'
down_revision: Union[str, Sequence[str], None] = '88655167d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('PatreonLink',
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('tg_username', sa.Text(), nullable=True),
    sa.Column('patreon_email', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['tg_id'], ['Users.tg_id'], name='fk_valid_tg_id'),
    sa.PrimaryKeyConstraint('tg_id'),
    sa.UniqueConstraint('patreon_email', name='Patreon_email_is_unique')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('PatreonLink')
