"""add size to items

Revision ID: f6g7h8i9j1k2
Revises: e5f6g7h8i9j1
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6g7h8i9j1k2'
down_revision: Union[str, None] = 'e5f6g7h8i9j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('size', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'size')