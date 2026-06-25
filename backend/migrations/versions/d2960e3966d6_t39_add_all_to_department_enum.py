"""t39 add 'all' company-wide value to department enum

Revision ID: d2960e3966d6
Revises: d4f5a6b7c8e9
Create Date: 2026-06-22 00:00:00.000000

Adds a company-wide "all" label to the shared `department` enum (T39). A
document tagged "all" is visible to every department in RAG retrieval; the
filter in rag/search.py matches `department IN (employee_department, 'all')`.

Notes:

* "all" is a document-scoping value only. employees.department must stay one
  of the seven real departments; that is enforced at the app layer (the schema
  Literals in api/schemas/admin.py and the DEPARTMENTS set in
  routers/employees.py), not by the DB, because the enum is shared by both
  employees.department and documents.department.
* `ADD VALUE IF NOT EXISTS` is idempotent and safe to re-run. It runs inside
  Alembic's transaction on PostgreSQL 12+ because the new label is not *used*
  within this migration (Render is PG 14+).
* downgrade is a no-op: PostgreSQL has no `ALTER TYPE ... DROP VALUE`. Removing
  the label would require recreating the type and rewriting both dependent
  columns, which is not worth it for an additive value. Documented per the
  T39 acceptance criteria.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2960e3966d6"
down_revision: str | None = "d4f5a6b7c8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE department ADD VALUE IF NOT EXISTS 'all'")


def downgrade() -> None:
    # PostgreSQL cannot drop an enum value. Leaving "all" in place on downgrade
    # is harmless: no employee row can hold it (app-layer gate), and the T28/T39
    # retrieval filter is unaffected by an unused label. See module docstring.
    pass
