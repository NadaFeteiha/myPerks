"""add HNSW index on document_chunks.embedding for fast vector search

Revision ID: a3f1d2e8b914
Revises: 96be68f88a51
Create Date: 2026-05-23 00:00:00.000000

Without this index every similarity search is a full sequential scan —
O(n) across all chunks.  The HNSW index (Hierarchical Navigable Small World)
gives approximate nearest-neighbour search in O(log n) at the cost of a
one-time build and slightly more storage.  Parameters are conservative
defaults suitable for up to ~1M vectors.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a3f1d2e8b914"
down_revision: str | None = "b5c4d3e2f1a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # m=16  : max connections per node — higher = better recall, more memory
    # ef_construction=64 : search width during build — higher = better quality
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
