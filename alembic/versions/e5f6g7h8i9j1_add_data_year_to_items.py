"""add data_year_start and data_year_end to items

Revision ID: e5f6g7h8i9j1
Revises: d3e4f5g6h7i8
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6g7h8i9j1'
down_revision: Union[str, None] = 'd3e4f5g6h7i8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('data_year_start', sa.Integer(), nullable=True))
    op.add_column('items', sa.Column('data_year_end', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'data_year_end')
    op.drop_column('items', 'data_year_start')