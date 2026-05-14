"""add auth, ratings, comments columns and new tables

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

    # Create new tables if they don't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            reporter_id INTEGER REFERENCES users(id),
            reported_user_id INTEGER REFERENCES users(id),
            report_type VARCHAR(255) NOT NULL,
            target_item_id INTEGER REFERENCES items(id),
            reason VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            reviewed_by INTEGER REFERENCES users(id),
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS visualization_links (
            id SERIAL PRIMARY KEY,
            parent_item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            owner_user_id INTEGER REFERENCES users(id),
            link_type VARCHAR(50) NOT NULL DEFAULT 'external',
            display_order INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            thumbnail_url TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('visualization_links')
    op.drop_table('reports')

    op.drop_column('ratings', 'user_id')
    op.drop_column('comments', 'created_at')
    op.drop_column('comments', 'author_name')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_active')
