"""add pdf_magnet_link and license_type to items

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, Sequence[str], None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pdf_magnet_link and license_type columns to items table."""
    op.add_column('items', sa.Column('pdf_magnet_link', sa.String(), nullable=True))
    op.add_column('items', sa.Column('license_type', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove pdf_magnet_link and license_type columns from items table."""
    op.drop_column('items', 'license_type')
    op.drop_column('items', 'pdf_magnet_link')
