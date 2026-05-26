"""Add authors to books.

Revision ID: 202605261030
Revises: 202605251600
Create Date: 2026-05-26 10:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "202605261030"
down_revision = "202605251600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("authors", sa.JSON(), nullable=True))

    books = sa.table("books", sa.column("authors", sa.JSON()))
    op.execute(books.update().where(books.c.authors.is_(None)).values(authors=[]))

    op.alter_column("books", "authors", nullable=False)


def downgrade() -> None:
    op.drop_column("books", "authors")
