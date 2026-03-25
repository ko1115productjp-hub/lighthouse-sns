"""add_notifications_table

Revision ID: fad3dbedb590
Revises: 1560eb354ac4
Create Date: 2026-03-25 01:10:42.786535+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fad3dbedb590"
down_revision = "1560eb354ac4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notifications table
    # The Enum type will be automatically created
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.Enum(
            "follow", "unfollow", "citation", "agreement", "output_follow",
            name="notification_type_enum",
            create_type=True
        ), nullable=False),
        sa.Column("output_id", sa.String(30), nullable=True),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["output_id"], ["outputs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_type", "notifications", ["type"])
    op.create_index("idx_notifications_is_read", "notifications", ["is_read"])
    op.create_index("idx_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_notifications_created_at", table_name="notifications")
    op.drop_index("idx_notifications_is_read", table_name="notifications")
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")

    # Drop table
    op.drop_table("notifications")

    # Drop enum
    op.execute("DROP TYPE notification_type_enum")
