"""add_pgvector_and_embedding

Revision ID: 7f8e9a0b1c2d
Revises: 5013e1f1a53a
Create Date: 2026-03-25 15:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = "7f8e9a0b1c2d"
down_revision = "5013e1f1a53a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to outputs table (1536 dimensions for text-embedding-3-small)
    op.add_column(
        "outputs",
        sa.Column(
            "content_embedding",
            Vector(1536),
            nullable=True,
            comment="OpenAI embedding vector for similarity search",
        ),
    )

    # Create index for vector similarity search (using HNSW for better performance)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_outputs_content_embedding_hnsw
        ON outputs USING hnsw (content_embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_outputs_content_embedding_hnsw")

    # Drop column
    op.drop_column("outputs", "content_embedding")

    # Note: We don't drop the extension as other tables might use it
