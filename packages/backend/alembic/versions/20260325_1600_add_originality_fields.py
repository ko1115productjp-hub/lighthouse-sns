"""add_originality_fields

Revision ID: 8a9b0c1d2e3f
Revises: 7f8e9a0b1c2d
Create Date: 2026-03-25 16:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8a9b0c1d2e3f"
down_revision = "7f8e9a0b1c2d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add originality score column (0-100)
    op.add_column(
        "outputs",
        sa.Column(
            "originality_score",
            sa.Integer,
            nullable=True,
            comment="Originality score from LLM judgment (0-100)",
        ),
    )

    # Add AI generation probability column (0-100)
    op.add_column(
        "outputs",
        sa.Column(
            "ai_generated_probability",
            sa.Integer,
            nullable=True,
            comment="Probability that content is AI-generated (0-100%)",
        ),
    )

    # Add originality warnings array column
    op.add_column(
        "outputs",
        sa.Column(
            "originality_warnings",
            postgresql.ARRAY(sa.Text),
            nullable=True,
            comment="Array of warning messages from originality checks",
        ),
    )


def downgrade() -> None:
    # Drop columns
    op.drop_column("outputs", "originality_warnings")
    op.drop_column("outputs", "ai_generated_probability")
    op.drop_column("outputs", "originality_score")
