"""add_imod_score_to_items

Revision ID: c2d3e4f5a6b7
Revises: b3c4d5e6f7g8
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('imod_score', sa.Float(), nullable=True))
    op.create_index('ix_items_imod_score', 'items', ['imod_score'])


def downgrade() -> None:
    op.drop_index('ix_items_imod_score', table_name='items')
    op.drop_column('items', 'imod_score')