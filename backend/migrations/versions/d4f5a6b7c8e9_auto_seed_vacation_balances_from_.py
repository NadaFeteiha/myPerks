"""auto-seed vacation balances from approved department policy

Revision ID: d4f5a6b7c8e9
Revises: c8e1f2a3b4d5
Create Date: 2026-06-18 00:00:00.000000

Whenever an employee row is inserted (HR pre-create, employee self-registration,
or a future Clerk re-link), a trigger looks up the employee's department's most
recently *approved* DocumentExtraction and seeds VacationBalance rows for the
current year from it -- falling back to the 15/10/5 company defaults if that
department has no approved policy yet.

Also backfills current-year balances for any employee who already exists but
is missing one or more leave-type rows, so the same rule applies retroactively
to old employees, not just new ones.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4f5a6b7c8e9"
down_revision: str | None = "c8e1f2a3b4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION seed_employee_vacation_balances(
            p_employee_id INTEGER,
            p_department department,
            p_year INTEGER
        ) RETURNS VOID AS $$
        DECLARE
            policy jsonb;
        BEGIN
            SELECT de.approved_data::jsonb INTO policy
            FROM document_extractions de
            JOIN documents d ON d.id = de.document_id
            WHERE d.department = p_department
              AND de.status = 'approved'
            ORDER BY de.reviewed_at DESC
            LIMIT 1;

            INSERT INTO vacation_balances
                (employee_id, leave_type, total_days, used_days, year)
            VALUES
                (p_employee_id, 'vacation',
                 COALESCE((policy->>'vacation_days')::numeric, 15), 0, p_year),
                (p_employee_id, 'sick',
                 COALESCE((policy->>'sick_days')::numeric, 10), 0, p_year),
                (p_employee_id, 'pto',
                 COALESCE((policy->>'pto_days')::numeric, 5), 0, p_year)
            ON CONFLICT (employee_id, year, leave_type) DO NOTHING;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_seed_vacation_balances_on_employee_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            PERFORM seed_employee_vacation_balances(
                NEW.id, NEW.department, EXTRACT(YEAR FROM now())::int
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS seed_vacation_balances_on_employee_insert ON employees
        """
    )
    op.execute(
        """
        CREATE TRIGGER seed_vacation_balances_on_employee_insert
        AFTER INSERT ON employees
        FOR EACH ROW
        EXECUTE FUNCTION trg_seed_vacation_balances_on_employee_insert()
        """
    )

    # Backfill: apply the same rule to employees who already exist today.
    op.execute(
        """
        SELECT seed_employee_vacation_balances(
            e.id, e.department, EXTRACT(YEAR FROM now())::int
        )
        FROM employees e
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS seed_vacation_balances_on_employee_insert ON employees"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS trg_seed_vacation_balances_on_employee_insert()"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "seed_employee_vacation_balances(INTEGER, department, INTEGER)"
    )
