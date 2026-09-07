"""add auth and interaction columns

Revision ID: a1b2c3d4e5f6
Revises: fa99e124f96c
Create Date: 2026-05-14 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fa99e124f96c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to users table
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')))

    # Add columns to comments table
    op.add_column('comments', sa.Column('author_name', sa.String(), nullable=True))
    op.add_column('comments', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')))

    # Add column to ratings table
    op.add_column('ratings', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute("ALTER TABLE ratings ADD CONSTRAINT fk_ratings_user_id FOREIGN KEY (user_id) REFERENCES users(id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ratings', 'user_id')
    op.drop_column('comments', 'created_at')
    op.drop_column('comments', 'author_name')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_active')
