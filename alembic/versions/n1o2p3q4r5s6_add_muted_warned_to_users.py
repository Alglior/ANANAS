"""add muted_until warned warnings to users

Revision ID: n1o2p3q4r5s6
Revises: m1n2o3p4q5r6
Create Date: 2026-07-25 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "n1o2p3q4r5s6"
down_revision = "m1n2o3p4q5r6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("muted_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("warned", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("warnings", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("users", "warnings")
    op.drop_column("users", "warned")
    op.drop_column("users", "muted_until")