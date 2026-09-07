"""add_pseudo_to_users

Revision ID: s1t2u3v4w5x6
Revises: 91228ef654a0
Create Date: 2026-07-30 12:00:00.000000

"""
import random
import string
import unicodedata

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 's1t2u3v4w5x6'
down_revision: Union[str, None] = '91228ef654a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def _generate_pseudo(prenom: str, nom: str, existing: set) -> str:
    base = f"{_normalize(prenom).lower()}-{_normalize(nom).lower().replace(' ', '-')}"
    while True:
        letters = ''.join(random.choices(string.ascii_lowercase, k=2))
        digits = ''.join(random.choices(string.digits, k=4))
        pseudo = f"{base}#{letters}{digits}"
        if pseudo not in existing:
            return pseudo


def upgrade() -> None:
    op.add_column('users', sa.Column('pseudo', sa.String(), nullable=True))

    conn = op.get_bind()
    meta = sa.MetaData()
    meta.reflect(only=('users',), bind=conn)
    users_table = sa.Table('users', meta)

    rows = conn.execute(sa.select(users_table.c.id, users_table.c.prenom, users_table.c.nom)).fetchall()
    existing_pseudos = {row.pseudo for row in conn.execute(sa.select(users_table.c.pseudo)).fetchall() if row.pseudo}

    for row in rows:
        pseudo = _generate_pseudo(row.prenom, row.nom, existing_pseudos)
        existing_pseudos.add(pseudo)
        conn.execute(
            sa.update(users_table).where(users_table.c.id == row.id).values(pseudo=pseudo)
        )

    op.alter_column('users', 'pseudo', nullable=False)
    op.create_unique_constraint('uq_users_pseudo', 'users', ['pseudo'])


def downgrade() -> None:
    op.drop_constraint('uq_users_pseudo', 'users', type_='unique')
    op.drop_column('users', 'pseudo')