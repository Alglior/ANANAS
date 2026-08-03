"""drop email column from users

Revision ID: x0y1z2w3v4u5
Revises: y0x1w2v3u4t5
Create Date: 2026-08-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'x0y1z2w3v4u5'
down_revision: Union[str, None] = 'y0x1w2v3u4t5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.drop_column('users', 'email')


def downgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.create_unique_constraint('users_email_key', 'users', ['email'])