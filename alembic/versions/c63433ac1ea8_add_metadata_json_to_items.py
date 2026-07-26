"""add_metadata_json_to_items

Revision ID: c63433ac1ea8
Revises: n1o2p3q4r5s6
Create Date: 2026-07-26 09:17:09.412480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c63433ac1ea8'
down_revision: Union[str, None] = 'n1o2p3q4r5s6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('items', sa.Column('metadata_json', sa.JSON(), server_default='[]', nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'metadata_json')