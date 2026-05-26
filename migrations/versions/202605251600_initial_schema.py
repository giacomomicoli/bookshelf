"""Initial schema.

Revision ID: 202605251600
Revises:
Create Date: 2026-05-25 16:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "202605251600"
down_revision = None
branch_labels = None
depends_on = None


book_format = postgresql.ENUM(
    "hardcover",
    "paperback",
    "mass_market_paperback",
    "ebook",
    "audiobook",
    "other",
    name="book_format",
    create_type=False,
)

reading_status = postgresql.ENUM(
    "unread",
    "reading",
    "read",
    name="reading_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    book_format.create(bind, checkfirst=True)
    reading_status.create(bind, checkfirst=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "sub_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "slug", name="uq_sub_categories_category_slug"),
    )
    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("sub_category_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("purchase_urls", sa.JSON(), nullable=False),
        sa.Column("thumbnail_object_key", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_source_url", sa.String(length=500), nullable=True),
        sa.Column("published_on", sa.Date(), nullable=True),
        sa.Column("edition", sa.String(length=255), nullable=True),
        sa.Column("format", book_format, nullable=True),
        sa.Column("page_length", sa.Integer(), nullable=True),
        sa.Column("reading_status", reading_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sub_category_id"], ["sub_categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("books")
    op.drop_table("sub_categories")
    op.drop_table("categories")

    bind = op.get_bind()
    reading_status.drop(bind, checkfirst=True)
    book_format.drop(bind, checkfirst=True)
