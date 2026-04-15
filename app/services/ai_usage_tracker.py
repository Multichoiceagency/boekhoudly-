"""Helper to track AI usage on a company's subscription."""
import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.ai_usage import AiUsage
from app.models.company_subscription import CompanySubscription
from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)


# Per-operation default credits (1 credit ≈ 1 chat message or 1 classification)
DEFAULT_CREDITS = {
    "chat": 2,
    "classify": 1,
    "extract": 3,
    "ocr": 5,
    "insights": 1,
}


async def track_ai_usage(
    db: AsyncSession,
    *,
    user: User,
    operation: str,
    model: Optional[str] = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    credits: Optional[int] = None,
    cost_eur_cents: int = 0,
) -> dict:
    """Record an AI usage event and increment subscription counters.

    Returns a dict with `over_quota: bool` and `credits_remaining: int` so
    callers can warn the user when they go past their plan's included credits.
    The call is non-blocking — usage is logged even if the user exceeds quota.
    """
    if not user.company_id:
        return {"tracked": False, "reason": "user has no company"}

    credits_used = credits if credits is not None else DEFAULT_CREDITS.get(operation, 1)

    # Log the event
    event = AiUsage(
        id=uuid.uuid4(),
        company_id=user.company_id,
        user_id=user.id,
        operation=operation,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        credits=credits_used,
        cost_eur_cents=cost_eur_cents,
    )
    db.add(event)

    # Increment subscription counters
    sub_result = await db.execute(
        select(CompanySubscription, SubscriptionPlan)
        .join(SubscriptionPlan, CompanySubscription.plan_id == SubscriptionPlan.id)
        .where(CompanySubscription.company_id == user.company_id)
    )
    row = sub_result.first()
    if not row:
        await db.flush()
        return {"tracked": True, "subscription": False, "credits_used": credits_used}

    sub, plan = row
    sub.ai_credits_used = (sub.ai_credits_used or 0) + credits_used
    sub.ai_cost_eur_cents = (sub.ai_cost_eur_cents or 0) + cost_eur_cents
    sub.updated_at = datetime.utcnow()
    await db.flush()

    over_quota = sub.ai_credits_used > plan.ai_credits_included
    remaining = max(0, plan.ai_credits_included - sub.ai_credits_used)
    return {
        "tracked": True,
        "credits_used": credits_used,
        "credits_remaining": remaining,
        "over_quota": over_quota,
        "plan": plan.slug,
    }
