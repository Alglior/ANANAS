"""add user_id to comments

Revision ID: c3d4e5f6g7h8
Revises: 32cff08a15b4
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6g7h8'
down_revision = '32cff08a15b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable user_id column first
    op.add_column('comments', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute("ALTER TABLE comments ADD CONSTRAINT fk_comments_user_id FOREIGN KEY (user_id) REFERENCES users(id)")

    # Populate existing comments by matching author_name with user full name
    op.execute(
        "UPDATE comments SET user_id = users.id "
        "FROM users "
        "WHERE comments.user_id IS NULL "
        "AND CONCAT(users.prenom, ' ', users.nom) = comments.author_name"
    )


def downgrade() -> None:
    op.drop_constraint('fk_comments_user_id', 'comments', type_='foreignkey')
    op.drop_column('comments', 'user_id')
