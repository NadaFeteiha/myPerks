"""fix datetime timezone awareness

Revision ID: eb2e08829171
Revises: a0543e57a96f
Create Date: 2026-05-26 00:32:37.000286

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "eb2e08829171"
down_revision: str | None = "a0543e57a96f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
