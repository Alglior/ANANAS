"""add_content_to_home_sections

Revision ID: y0x1w2v3u4t5
Revises: z0y1x2w3v4u5
Create Date: 2026-08-01 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'y0x1w2v3u4t5'
down_revision: Union[str, None] = 'z0y1x2w3v4u5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('home_sections', sa.Column('content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('home_sections', 'content')