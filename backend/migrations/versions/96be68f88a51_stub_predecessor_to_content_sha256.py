"""stub — predecessor revision applied to Neon before 31c00c3e4441 was finalized

This revision existed in the database but its file was not committed.
The upgrade it originally performed is handled idempotently by 31c00c3e4441.

Revision ID: 96be68f88a51
Revises: f140fceba154
Create Date: 2026-05-21 00:00:00.000000

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "96be68f88a51"
down_revision: str | None = "f140fceba154"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
