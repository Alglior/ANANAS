"""add_email_verified_and_verification_token

Revision ID: r0s1t2u3v4w5
Revises: q5r6s7t8u9v0
Create Date: 2026-07-30 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'r0s1t2u3v4w5'
down_revision: Union[str, None] = 'q5r6s7t8u9v0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('verification_token', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')
