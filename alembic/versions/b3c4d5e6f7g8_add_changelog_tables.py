"""add_changelog_tables

Revision ID: b3c4d5e6f7g8
Revises: a1b2c3d4e5f7
Create Date: 2026-08-15

"""
from alembic import op
import sqlalchemy as sa


revision = 'b3c4d5e6f7g8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('changelog_versions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('changelog_sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('version_id', sa.Integer(), sa.ForeignKey('changelog_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('items', sa.Text(), server_default='[]', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
    )


def downgrade():
    op.drop_table('changelog_sections')
    op.drop_table('changelog_versions')
