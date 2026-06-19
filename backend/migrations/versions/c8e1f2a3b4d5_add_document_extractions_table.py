"""add document_extractions table

Revision ID: c8e1f2a3b4d5
Revises: f14048641b09
Create Date: 2026-06-16 00:00:00.000000

Stores the LLM-extracted HR policy snapshot for each document.
HR reviews, edits, and approves before the values are applied
to VacationBalance rows for the document's department.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c8e1f2a3b4d5"
down_revision: str | None = "f14048641b09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use raw SQL to avoid SQLAlchemy auto-creating the enum type
    # (it already exists from a prior partial run).
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'extraction_status'
            ) THEN
                CREATE TYPE extraction_status AS ENUM
                    ('pending', 'extracting', 'extracted', 'approved', 'failed');
            END IF;
        END $$
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_extractions (
            id              SERIAL PRIMARY KEY,
            document_id     INTEGER NOT NULL UNIQUE
                                REFERENCES documents(id) ON DELETE CASCADE,
            status          extraction_status NOT NULL DEFAULT 'pending',
            extracted_data  TEXT,
            approved_data   TEXT,
            reviewed_by     INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            reviewed_at     TIMESTAMPTZ,
            error_message   TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_document_extractions_document_id
        ON document_extractions (document_id)
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_extractions_document_id", table_name="document_extractions"
    )
    op.drop_table("document_extractions")
    op.execute("DROP TYPE extraction_status")
