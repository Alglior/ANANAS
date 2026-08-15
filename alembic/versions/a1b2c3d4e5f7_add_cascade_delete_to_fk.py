"""add_cascade_delete_to_fk

Revision ID: a1b2c3d4e5f7
Revises: z0y1x2w3v4u5
Create Date: 2026-08-15

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f7"
down_revision = "x0y1z2w3v4u5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("data_chunks_parent_item_id_fkey", "data_chunks", type_="foreignkey")
    op.create_foreign_key(
        "data_chunks_parent_item_id_fkey",
        "data_chunks",
        "items",
        ["parent_item_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("user_uploads_parent_item_id_fkey", "user_uploads", type_="foreignkey")
    op.create_foreign_key(
        "user_uploads_parent_item_id_fkey",
        "user_uploads",
        "items",
        ["parent_item_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("user_uploads_published_item_id_fkey", "user_uploads", type_="foreignkey")
    op.create_foreign_key(
        "user_uploads_published_item_id_fkey",
        "user_uploads",
        "items",
        ["published_item_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("reports_target_item_id_fkey", "reports", type_="foreignkey")
    op.create_foreign_key(
        "reports_target_item_id_fkey",
        "reports",
        "items",
        ["target_item_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("reports_target_item_id_fkey", "reports", type_="foreignkey")
    op.create_foreign_key(
        "reports_target_item_id_fkey",
        "reports",
        "items",
        ["target_item_id"],
        ["id"],
    )

    op.drop_constraint("user_uploads_published_item_id_fkey", "user_uploads", type_="foreignkey")
    op.create_foreign_key(
        "user_uploads_published_item_id_fkey",
        "user_uploads",
        "items",
        ["published_item_id"],
        ["id"],
    )

    op.drop_constraint("user_uploads_parent_item_id_fkey", "user_uploads", type_="foreignkey")
    op.create_foreign_key(
        "user_uploads_parent_item_id_fkey",
        "user_uploads",
        "items",
        ["parent_item_id"],
        ["id"],
    )

    op.drop_constraint("data_chunks_parent_item_id_fkey", "data_chunks", type_="foreignkey")
    op.create_foreign_key(
        "data_chunks_parent_item_id_fkey",
        "data_chunks",
        "items",
        ["parent_item_id"],
        ["id"],
    )
