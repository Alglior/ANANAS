"""remove visibility and is_published from data_chunks

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove visibility and is_published columns from data_chunks table."""
    op.drop_column('data_chunks', 'visibility')
    op.drop_column('data_chunks', 'is_published')


def downgrade() -> None:
    """Restore visibility and is_published columns to data_chunks table."""
    op.add_column('data_chunks', sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('data_chunks', sa.Column('visibility', sa.String(), nullable=False, server_default='public'))
