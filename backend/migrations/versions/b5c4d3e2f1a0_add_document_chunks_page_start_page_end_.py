"""add document_chunks page_start page_end for citations

Revision ID: b5c4d3e2f1a0
Revises: 31c00c3e4441
Create Date: 2026-05-21 16:25:07.894579

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5c4d3e2f1a0"
down_revision: str | None = "31c00c3e4441"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_start INTEGER"
        )
    )
    op.execute(
        sa.text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_end INTEGER")
    )


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE document_chunks DROP COLUMN IF EXISTS page_end"))
    op.execute(sa.text("ALTER TABLE document_chunks DROP COLUMN IF EXISTS page_start"))
