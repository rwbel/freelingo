"""Shared subscription access and quota helpers.

These functions are the single source of truth for subscription access control.
- is_subscribed(): Returns True for users with "trialing" or "active" subscription status.
  (When RevenueCat is the only billing authority, this reflects RevenueCat sync.)
- Freemium quotas and trials apply to all users.
  Subscribed users bypass all freemium quotas.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def is_subscribed(user: User) -> bool:
    """Return True if the user has full access to AI features.

    Only "trialing" or "active" subscription status passes.
    """
    # Renewal notifications can lag behind the cached period end. Only a verified
    # synchronization changes access; the local clock must not revoke it.
    return user.subscription_status in ("trialing", "active")


async def apply_subscription_quotas(user: User, db: AsyncSession, *, commit: bool = True) -> None:
    """Set default quotas when a subscription becomes active or trialing."""
    user.conversation_weekly_sessions = settings.DEFAULT_CONVERSATION_WEEKLY_SESSIONS
    user.conversation_weekly_minutes = settings.DEFAULT_CONVERSATION_WEEKLY_MINUTES
    user.conversation_daily_minutes = settings.DEFAULT_CONVERSATION_DAILY_MINUTES
    user.monthly_tokens_limit = settings.DEFAULT_MONTHLY_TOKENS_LIMIT
    user.conversation_max_duration = settings.DEFAULT_CONVERSATION_MAX_DURATION
    user.conversation_inactivity_timeout = settings.DEFAULT_CONVERSATION_INACTIVITY_TIMEOUT
    if commit:
        await db.commit()
