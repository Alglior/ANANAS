"""add owner_user_id to items

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-05-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('owner_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_items_owner_user_id',
        'items', 'users',
        ['owner_user_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_items_owner_user_id', 'items', type_='foreignkey')
    op.drop_column('items', 'owner_user_id')
