"""add user locations for news about meetups

Revision ID: 3228656f462e
Revises: 4d24102547b1
Create Date: 2026-04-24 23:22:34.731284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3228656f462e'
down_revision: Union[str, Sequence[str], None] = '4d24102547b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Location',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('country_name', sa.Text(), nullable=False),
    sa.Column('city_name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('country_name', 'city_name', name='Unique_city_per_country')
    )
    op.create_table('UserLocation',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['Location.id'], name='user_location_valid_location_id'),
    sa.ForeignKeyConstraint(['tg_id'], ['Users.tg_id'], name='user_location_valid_tg_id'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tg_id', 'location_id', name='Unique_location_per_user')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('UserLocation')
    op.drop_table('Location')
