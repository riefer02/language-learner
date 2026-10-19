"""Add the learning core: users, items, review cards, review logs.

Revision ID: 20261019_0002
Revises: 20261019_0001
Create Date: 2026-10-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_0002"
down_revision = "20261019_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_local", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_user_is_local", "user", ["is_local"], unique=False)
    op.create_index("ix_user_created_at", "user", ["created_at"], unique=False)

    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("korean", sa.String(length=300), nullable=False),
        sa.Column("english", sa.String(length=300), nullable=False),
        sa.Column("romanization", sa.String(length=300), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("freq_rank", sa.Integer(), nullable=True),
        sa.Column("audio_path", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("default_skill", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "korean", "english", "item_type", name="uq_item_content"
        ),
    )
    op.create_index("ix_item_level", "item", ["level"], unique=False)
    op.create_index("ix_item_created_at", "item", ["created_at"], unique=False)
    op.create_index(
        "ix_item_level_type", "item", ["level", "item_type"], unique=False
    )

    op.create_table(
        "review_card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=20), nullable=False),
        sa.Column("state", sa.Integer(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "item_id",
            "skill",
            name="uq_review_card_user_item_skill",
        ),
    )
    op.create_index("ix_review_card_due_at", "review_card", ["due_at"])
    op.create_index(
        "ix_review_card_due", "review_card", ["user_id", "due_at"]
    )

    op.create_table(
        "review_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("scheduled_days", sa.Float(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["card_id"], ["review_card.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_log_user_date", "review_log", ["user_id", "reviewed_at"]
    )


def downgrade():
    op.drop_index("ix_review_log_user_date", table_name="review_log")
    op.drop_table("review_log")
    op.drop_index("ix_review_card_due", table_name="review_card")
    op.drop_index("ix_review_card_due_at", table_name="review_card")
    op.drop_table("review_card")
    op.drop_index("ix_item_level_type", table_name="item")
    op.drop_index("ix_item_created_at", table_name="item")
    op.drop_index("ix_item_level", table_name="item")
    op.drop_table("item")
    op.drop_index("ix_user_created_at", table_name="user")
    op.drop_index("ix_user_is_local", table_name="user")
    op.drop_table("user")
