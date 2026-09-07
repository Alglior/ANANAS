"""add parent_id to comments (threaded replies)

Revision ID: o1p2q3r4s5t6
Revises: d7e8f9g0h1i2
Create Date: 2026-07-26

"""
from alembic import op
import sqlalchemy as sa

revision = 'o1p2q3r4s5t6'
down_revision = 'd7e8f9g0h1i2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists (it may have been added by _run_migrations)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("comments")]
    if "parent_id" not in columns:
        op.add_column('comments', sa.Column('parent_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_comments_parent_id', 'comments', 'comments',
            ['parent_id'], ['id'], ondelete='CASCADE'
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("comments")]
    if "parent_id" in columns:
        try:
            op.drop_constraint('fk_comments_parent_id', 'comments', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('comments', 'parent_id')