"""add_referenced_entity_fields_to_outputs

Revision ID: a1b2c3d4e5f6
Revises: fad3dbedb590
Create Date: 2026-03-25 14:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "fad3dbedb590"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to category_enum
    op.execute("ALTER TYPE category_enum ADD VALUE IF NOT EXISTS 'SCRIPT'")
    op.execute("ALTER TYPE category_enum ADD VALUE IF NOT EXISTS 'PLACE'")
    op.execute("ALTER TYPE category_enum ADD VALUE IF NOT EXISTS 'EXPERIENCE'")

    # Add referenced_entity_type column
    op.add_column(
        "outputs",
        sa.Column(
            "referenced_entity_type",
            sa.String(length=20),
            nullable=True,
            comment="Type of referenced entity: place, book, movie, stage, concert",
        ),
    )

    # Add referenced_entity_id column
    op.add_column(
        "outputs",
        sa.Column(
            "referenced_entity_id",
            sa.String(length=255),
            nullable=True,
            comment="External API ID (Google Place ID, ISBN, TMDb ID, etc.)",
        ),
    )

    # Add referenced_entity_data column (JSONB for flexible metadata storage)
    op.add_column(
        "outputs",
        sa.Column(
            "referenced_entity_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Metadata from external APIs (name, address, photos, etc.)",
        ),
    )

    # Create index on referenced_entity_type for filtering
    op.create_index(
        "ix_outputs_referenced_entity_type",
        "outputs",
        ["referenced_entity_type"],
        unique=False,
    )

    # Create index on referenced_entity_id for lookups
    op.create_index(
        "ix_outputs_referenced_entity_id",
        "outputs",
        ["referenced_entity_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_outputs_referenced_entity_id", table_name="outputs")
    op.drop_index("ix_outputs_referenced_entity_type", table_name="outputs")

    # Drop columns
    op.drop_column("outputs", "referenced_entity_data")
    op.drop_column("outputs", "referenced_entity_id")
    op.drop_column("outputs", "referenced_entity_type")

    # Note: Cannot remove enum values in downgrade (PostgreSQL limitation)
    # New enum values will remain
