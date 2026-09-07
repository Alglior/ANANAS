"""remove is_published from items

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove is_published column from items table."""
    op.drop_column('items', 'is_published')


def downgrade() -> None:
    """Restore is_published column to items table."""
    op.add_column('items', sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'))
