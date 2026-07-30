"""add catalogue_config table and migrate existing data

Revision ID: 91228ef654a0
Revises: r0s1t2u3v4w5
Create Date: 2026-07-30 04:14:29.991479

"""
import json
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '91228ef654a0'
down_revision: Union[str, None] = 'r0s1t2u3v4w5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_json_config():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "catalogues_config.json"
    )
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"donnees": True, "cartes": True, "applications": True}


def upgrade() -> None:
    op.create_table('catalogue_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('catalogue_type', sa.String(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('catalogue_type')
    )

    catalogues = _load_json_config()
    from sqlalchemy.sql import table, column
    from sqlalchemy import String, Boolean
    catalogue_config = table(
        'catalogue_config',
        column('catalogue_type', String),
        column('enabled', Boolean),
    )
    op.bulk_insert(catalogue_config, [
        {"catalogue_type": k, "enabled": v} for k, v in catalogues.items()
    ])


def downgrade() -> None:
    op.drop_table('catalogue_config')