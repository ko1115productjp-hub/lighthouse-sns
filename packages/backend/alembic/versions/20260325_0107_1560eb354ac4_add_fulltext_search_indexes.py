"""add_fulltext_search_indexes

Revision ID: 1560eb354ac4
Revises: 9c1cab355ad6
Create Date: 2026-03-25 01:07:41.377535+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1560eb354ac4"
down_revision = "9c1cab355ad6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram similarity search (must be first)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Add GIN index for full-text search on outputs.content
    # Using to_tsvector for English language full-text search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_outputs_content_fts
        ON outputs USING gin(to_tsvector('english', content))
        """
    )

    # Add GIN index for array search on tags
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_outputs_tags_gin
        ON outputs USING gin(tags)
        """
    )

    # Add indexes for user search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_username_trgm
        ON users USING gin(username gin_trgm_ops)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_display_name_trgm
        ON users USING gin(display_name gin_trgm_ops)
        """
    )


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_outputs_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_outputs_tags_gin")
    op.execute("DROP INDEX IF EXISTS idx_users_username_trgm")
    op.execute("DROP INDEX IF EXISTS idx_users_display_name_trgm")
