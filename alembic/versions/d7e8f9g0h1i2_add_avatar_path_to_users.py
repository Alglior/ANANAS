"""add_avatar_path_to_users

Revision ID: d7e8f9g0h1i2
Revises: c63433ac1ea8
Create Date: 2026-07-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7e8f9g0h1i2'
down_revision: Union[str, None] = 'c63433ac1ea8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_path')