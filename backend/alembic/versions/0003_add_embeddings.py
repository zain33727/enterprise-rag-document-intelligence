"""add pgvector embeddings

Revision ID: 0003_add_embeddings
Revises: 0002_add_document_content
"""
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "0003_add_embeddings"
down_revision = "0002_add_document_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("document_chunks", sa.Column("embedding", Vector(384), nullable=True))
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_embedding_hnsw", table_name="document_chunks")
    op.drop_column("document_chunks", "embedding")
