"""add_admin_audit_table

Revision ID: 32cff08a15b4
Revises: b2c3d4e5f6g7
Create Date: 2026-05-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '32cff08a15b4'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('admin_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('admin_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('target_type', sa.String(), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('details', postgresql.JSON(server_default='{}'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Index('ix_admin_audit_admin_user_id', 'admin_user_id'),
        sa.Index('ix_admin_audit_action_type', 'action_type'),
    )


def downgrade():
    op.drop_table('admin_audit')
