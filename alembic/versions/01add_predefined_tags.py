"""add predefined tag tables

Revision ID: 01add_predefined_tags
Revises: v1w2x3y4z5a6
Create Date: 2026-08-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '01add_predefined_tags'
down_revision: Union[str, None] = 'v1w2x3y4z5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    if not inspector.has_table("predefined_tag_categories"):
        op.create_table('predefined_tag_categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
    if not inspector.has_table("predefined_tags"):
        op.create_table('predefined_tags',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['category_id'], ['predefined_tag_categories.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('predefined_tags')
    op.drop_table('predefined_tag_categories')