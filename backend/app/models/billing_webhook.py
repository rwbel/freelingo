"""RevenueCat webhook receipt model for idempotent webhook processing."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RevenueCatWebhookReceipt(Base):
    """Stores processed RevenueCat webhook event IDs to prevent duplicate processing.

    Each event ID is stored once; the unique constraint on event_id ensures
    idempotent handling of retried webhooks.
    """

    __tablename__ = "revenuecat_webhook_receipts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(30), nullable=False)  # ISO format timestamp
