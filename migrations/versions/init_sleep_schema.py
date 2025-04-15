"""Initial sleep data schema.

Revision ID: 001
Revises:
Create Date: 2025-04-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade function for the sleep data schema."""
    # Create sleep_records table
    op.create_table(
        "sleep_records",
        sa.Column("record_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("sleep_start", sa.DateTime(), nullable=False),
        sa.Column("sleep_end", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("sleep_phases", JSON, nullable=True),
        sa.Column("sleep_quality", sa.Integer(), nullable=True),
        sa.Column("heart_rate", JSON, nullable=True),
        sa.Column("breathing", JSON, nullable=True),
        sa.Column("environment", JSON, nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("meta_data", JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("record_id"),
    )

    # Create index on user_id and date for faster queries
    op.create_index(
        op.f("ix_sleep_records_user_id"), "sleep_records", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_sleep_records_date"), "sleep_records", ["date"], unique=False
    )

    # Create sleep_time_series table
    op.create_table(
        "sleep_time_series",
        sa.Column("point_id", sa.String(), nullable=False),
        sa.Column("sleep_record_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("heart_rate", sa.Float(), nullable=True),
        sa.Column("movement", sa.Float(), nullable=True),
        sa.Column("respiration_rate", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sleep_record_id"], ["sleep_records.record_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("point_id"),
    )

    # Create index on sleep_record_id for faster joins
    op.create_index(
        op.f("ix_sleep_time_series_sleep_record_id"),
        "sleep_time_series",
        ["sleep_record_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade function for the sleep data schema."""
    # Drop tables in reverse order
    op.drop_table("sleep_time_series")
    op.drop_table("sleep_records")
