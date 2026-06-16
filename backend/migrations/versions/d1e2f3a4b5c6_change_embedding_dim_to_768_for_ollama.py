"""change embedding dim to 768 for nomic-embed-text (Ollama)

Revision ID: d1e2f3a4b5c6
Revises: c8e1f2a3b4d5
Create Date: 2026-06-16 00:01:00.000000

nomic-embed-text outputs 768-dim vectors; text-embedding-3-small outputs 1536.
Drops existing chunk embeddings (they were zeros from mock mode anyway) and
resizes the column so pgvector accepts the new dimension.
The HNSW index is rebuilt on the new dimension.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c8e1f2a3b4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Null out existing embeddings — they were 1536-dim zeros from mock mode
    # and are incompatible with the new 768-dim column.
    op.execute("UPDATE document_chunks SET embedding = NULL")

    # Drop the HNSW index before altering the column type
    op.execute("DROP INDEX IF EXISTS hnsw_document_chunks_embedding")

    # Resize the column from vector(1536) to vector(768)
    op.execute(
        "ALTER TABLE document_chunks "
        "ALTER COLUMN embedding TYPE vector(768) USING NULL"
    )

    # Recreate the HNSW index for the new dimension
    op.execute(
        """
        CREATE INDEX hnsw_document_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("UPDATE document_chunks SET embedding = NULL")
    op.execute("DROP INDEX IF EXISTS hnsw_document_chunks_embedding")
    op.execute(
        "ALTER TABLE document_chunks "
        "ALTER COLUMN embedding TYPE vector(1536) USING NULL"
    )
    op.execute(
        """
        CREATE INDEX hnsw_document_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )
