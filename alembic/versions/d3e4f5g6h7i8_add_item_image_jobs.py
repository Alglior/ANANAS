"""add_item_image_jobs

Revision ID: d3e4f5g6h7i8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3e4f5g6h7i8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'item_image_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('magnet_link', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0'),
        sa.Column('details', sa.String(), nullable=True),
    )
    op.create_index('ix_item_image_jobs_item_id', 'item_image_jobs', ['item_id'])


def downgrade() -> None:
    op.drop_index('ix_item_image_jobs_item_id', table_name='item_image_jobs')
    op.drop_table('item_image_jobs')