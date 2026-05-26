"""add documents.content_sha256 for ingestion dedup

Revision ID: 31c00c3e4441
Revises: 96be68f88a51
Create Date: 2026-05-21 12:25:49.064026

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31c00c3e4441"
down_revision: str | None = "96be68f88a51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use IF NOT EXISTS so this is safe on databases that already have the column
    # from the predecessor revision (96be68f88a51) applied during development.
    op.execute(
        sa.text(
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS"
            " content_sha256 VARCHAR(64)"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_content_sha256"
            " ON documents (content_sha256)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_documents_content_sha256"))
    op.execute(sa.text("ALTER TABLE documents DROP COLUMN IF EXISTS content_sha256"))
