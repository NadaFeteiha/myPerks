"""t21 add roles, employee fields, document department, shared department enum

Revision ID: f14048641b09
Revises: f2e4c4a28dcc
Create Date: 2026-06-09 12:53:59.910875

Keystone schema migration for Cycle 2 (HR Admin side). All of Cycle 2 depends
on this landing first.

Why each step is shaped the way it is:

* This migration runs BEFORE db/seed.py (seed clears + repopulates afterwards),
  so the 3 existing Cycle 1 employees are still present with free-text, mixed-
  case departments ("Engineering", "Human Resources", "Marketing"). We must
  normalise those to valid enum labels before casting, or the USING cast fails.
* employees.department converts String(128) -> department enum and becomes
  NOT NULL: department-scoped RAG (T28) returns nothing for an employee with no
  department, so the column can't be optional.
* clerk_user_id becomes nullable: HR pre-creates an employee row (email +
  department) before that person ever logs in; the row is linked by email on
  first Clerk login (T25 / T27). It can't be NOT NULL.
* joined_date / benefits_year_reset are NOT NULL with no model-level default
  (set at onboarding). To satisfy the constraint for the pre-existing rows we
  add each column with a throwaway DEFAULT, then DROP the default so the live
  schema matches the model. Those placeholder rows are deleted by the seed
  immediately afterwards anyway.
* documents.department is NOT NULL with no company-wide tier; existing rows are
  backfilled to 'other'.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f14048641b09"
down_revision: str | None = "f2e4c4a28dcc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- enum types -------------------------------------------------------
    op.execute("CREATE TYPE employee_role AS ENUM ('employee', 'hr_admin')")
    op.execute(
        """
        CREATE TYPE department AS ENUM (
            'engineering', 'sales', 'marketing',
            'hr', 'finance', 'operations', 'other'
        )
        """
    )

    # --- employees.role ---------------------------------------------------
    # server default 'employee' fills existing rows automatically and matches
    # the model's server_default; we keep the default in place.
    op.execute(
        "ALTER TABLE employees "
        "ADD COLUMN role employee_role NOT NULL DEFAULT 'employee'"
    )

    # --- employees.department: normalise -> cast -> NOT NULL --------------
    # Resolve case/typos on existing free-text values before the cast.
    op.execute(
        "UPDATE employees SET department = lower(btrim(department)) "
        "WHERE department IS NOT NULL"
    )
    op.execute(
        "UPDATE employees SET department = 'hr' "
        "WHERE department IN ('human resources', 'people', "
        "'people ops', 'people operations')"
    )
    # Anything still unrecognised (or NULL) falls back to 'other'.
    op.execute(
        """
        UPDATE employees SET department = 'other'
        WHERE department IS NULL
           OR department NOT IN (
               'engineering', 'sales', 'marketing',
               'hr', 'finance', 'operations', 'other'
           )
        """
    )
    op.execute(
        "ALTER TABLE employees "
        "ALTER COLUMN department TYPE department USING department::department"
    )
    op.execute("ALTER TABLE employees ALTER COLUMN department SET NOT NULL")

    # --- employees.clerk_user_id: allow NULL (pre-create / link-by-email) -
    op.execute("ALTER TABLE employees ALTER COLUMN clerk_user_id DROP NOT NULL")

    # --- employees.joined_date / benefits_year_reset ----------------------
    # Throwaway DEFAULT satisfies NOT NULL for pre-existing rows, then dropped
    # so the schema matches the model (no server default; set at onboarding).
    op.execute(
        "ALTER TABLE employees "
        "ADD COLUMN joined_date date NOT NULL DEFAULT CURRENT_DATE"
    )
    op.execute("ALTER TABLE employees ALTER COLUMN joined_date DROP DEFAULT")
    op.execute(
        "ALTER TABLE employees "
        "ADD COLUMN benefits_year_reset date NOT NULL DEFAULT CURRENT_DATE"
    )
    op.execute("ALTER TABLE employees ALTER COLUMN benefits_year_reset DROP DEFAULT")

    # --- documents.department: backfill existing rows to 'other' ----------
    op.execute(
        "ALTER TABLE documents "
        "ADD COLUMN department department NOT NULL DEFAULT 'other'"
    )
    op.execute("ALTER TABLE documents ALTER COLUMN department DROP DEFAULT")


def downgrade() -> None:
    # Reverse order. NOTE: restoring clerk_user_id NOT NULL will fail if any
    # pre-created (unlinked) employee rows exist — that's expected; the
    # pre-create model has no clean downgrade once such rows are present.

    # --- documents --------------------------------------------------------
    op.execute("ALTER TABLE documents DROP COLUMN department")

    # --- employees --------------------------------------------------------
    op.execute("ALTER TABLE employees DROP COLUMN benefits_year_reset")
    op.execute("ALTER TABLE employees DROP COLUMN joined_date")
    op.execute("ALTER TABLE employees ALTER COLUMN clerk_user_id SET NOT NULL")
    op.execute("ALTER TABLE employees ALTER COLUMN department DROP NOT NULL")
    op.execute(
        "ALTER TABLE employees "
        "ALTER COLUMN department TYPE varchar(128) USING department::text"
    )
    op.execute("ALTER TABLE employees DROP COLUMN role")

    # --- enum types (after all dependent columns are gone/converted) ------
    op.execute("DROP TYPE department")
    op.execute("DROP TYPE employee_role")
