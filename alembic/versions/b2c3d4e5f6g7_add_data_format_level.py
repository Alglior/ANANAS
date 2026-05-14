"""add data_format_level to items

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('items', sa.Column('data_format_level', sa.String(), nullable=True, server_default='individual'))
    op.execute("UPDATE items SET data_format_level = 'individual' WHERE data_format_level IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('items', 'data_format_level')
