"""Add Stripe subscription fields

Revision ID: 0016_stripe_subscription
Revises: 0015_user_learning_profile
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_stripe_subscription"
down_revision: str | None = "0015_user_learning_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stripe_subscription_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stripe_price_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stripe_current_period_end", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("stripe_cancel_at_period_end", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "stripe_cancel_at_period_end")
    op.drop_column("users", "stripe_current_period_end")
    op.drop_column("users", "stripe_price_id")
    op.drop_column("users", "stripe_subscription_status")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
