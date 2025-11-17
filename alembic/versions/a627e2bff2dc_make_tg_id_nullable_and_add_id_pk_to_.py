"""make tg_id nullable and add id PK to MembershipByActivity

Revision ID: a627e2bff2dc
Revises: fab91702602c
Create Date: 2025-11-17 14:44:03.313966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a627e2bff2dc'
down_revision: Union[str, Sequence[str], None] = 'fab91702602c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

"""Make tg_id nullable and add id primary key to MembershipByActivity"""


def upgrade():
    op.add_column(
        'MembershipByActivity',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True)
    )

    op.drop_constraint(
        'MembershipByActivity_pkey',
        'MembershipByActivity',
        type_='primary'
    )

    # if tg_id is Null, this means the user never started the bot
    op.alter_column(
        'MembershipByActivity',
        'tg_id',
        existing_type=sa.Text(),
        nullable=True
    )

    op.create_primary_key(
        'MembershipByActivity_pkey',
        'MembershipByActivity',
        ['id']
    )

    op.create_unique_constraint(
        'uq_membership_tg_id',
        'MembershipByActivity',
        ['tg_id']
    )


def downgrade():
    op.drop_constraint('uq_membership_tg_id', 'MembershipByActivity', type_='unique')
    op.drop_constraint('MembershipByActivity_pkey', 'MembershipByActivity', type_='primary')
    op.alter_column(
        'MembershipByActivity',
        'tg_id',
        existing_type=sa.Text(),
        nullable=False
    )
    op.create_primary_key(
        'MembershipByActivity_pkey',
        'MembershipByActivity',
        ['tg_id']
    )
    op.drop_column('MembershipByActivity', 'id')
