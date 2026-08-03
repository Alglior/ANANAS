"""add_home_sections

Revision ID: z0y1x2w3v4u5
Revises: w1x2y3z4a5b6
Create Date: 2026-08-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'z0y1x2w3v4u5'
down_revision: Union[str, None] = 'w1x2y3z4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('home_sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_type', sa.String(), unique=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('is_builtin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('home_sections')