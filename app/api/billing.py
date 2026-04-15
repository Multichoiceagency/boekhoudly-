import uuid
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.subscription_plan import SubscriptionPlan
from app.models.company_subscription import CompanySubscription
from app.models.ai_usage import AiUsage
from app.utils.auth import get_current_user
from app.config import get_settings
from app.services import stripe_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])
settings = get_settings()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen admins hebben toegang")
    return current_user


def _plan_to_dict(p: SubscriptionPlan) -> dict:
    return {
        "id": str(p.id),
        "slug": p.slug,
        "name": p.name,
        "description": p.description,
        "monthly_eur": float(p.monthly_eur),
        "ai_credits_included": p.ai_credits_included,
        "ai_overage_eur_cents": p.ai_overage_eur_cents,
        "max_users": p.max_users,
        "features": p.features or {},
        "is_active": p.is_active,
    }


def _subscription_summary(sub: CompanySubscription, plan: SubscriptionPlan, company: Company) -> dict:
    base_cost = float(sub.monthly_eur_override) if sub.monthly_eur_override is not None else float(plan.monthly_eur)
    overage_credits = max(0, sub.ai_credits_used - plan.ai_credits_included)
    overage_cost = (overage_credits * plan.ai_overage_eur_cents) / 100
    ai_cost_actual = sub.ai_cost_eur_cents / 100
    total = base_cost + max(overage_cost, ai_cost_actual - (plan.ai_credits_included * plan.ai_overage_eur_cents / 100))
    return {
        "subscription_id": str(sub.id),
        "company": {
            "id": str(company.id),
            "name": company.name,
            "kvk_number": company.kvk_number,
        },
        "plan": {
            "id": str(plan.id),
            "slug": plan.slug,
            "name": plan.name,
            "monthly_eur": float(plan.monthly_eur),
            "ai_credits_included": plan.ai_credits_included,
            "ai_overage_eur_cents": plan.ai_overage_eur_cents,
        },
        "base_cost_eur": round(base_cost, 2),
        "ai_credits_used": sub.ai_credits_used,
        "ai_credits_included": plan.ai_credits_included,
        "ai_overage_credits": overage_credits,
        "ai_overage_eur": round(overage_cost, 2),
        "total_eur": round(base_cost + overage_cost, 2),
        "period_start": sub.period_start.isoformat() if sub.period_start else None,
        "period_end": sub.period_end.isoformat() if sub.period_end else None,
        "status": sub.status,
        "accountant_id": str(sub.accountant_id) if sub.accountant_id else None,
    }


@router.get("/plans")
async def list_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lijst van beschikbare abonnementen."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.sort_order)
    )
    plans = result.scalars().all()
    return [_plan_to_dict(p) for p in plans]


@router.get("/summary")
async def billing_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Maandoverzicht voor alle bedrijven die de huidige user mag zien.

    - admin: alle bedrijven
    - accountant: bedrijven waarvan hij accountant is
    - user: alleen z'n eigen company
    """
    q = select(CompanySubscription, SubscriptionPlan, Company).join(
        SubscriptionPlan, CompanySubscription.plan_id == SubscriptionPlan.id
    ).join(Company, CompanySubscription.company_id == Company.id)

    if current_user.role == "admin":
        pass  # all
    elif current_user.role == "accountant":
        q = q.where(CompanySubscription.accountant_id == current_user.id)
    else:
        if not current_user.company_id:
            return {"companies": [], "totals": {"base": 0, "ai_overage": 0, "total": 0, "count": 0}}
        q = q.where(CompanySubscription.company_id == current_user.company_id)

    result = await db.execute(q)
    rows = result.all()

    summaries = [_subscription_summary(sub, plan, company) for sub, plan, company in rows]
    totals = {
        "base": round(sum(s["base_cost_eur"] for s in summaries), 2),
        "ai_overage": round(sum(s["ai_overage_eur"] for s in summaries), 2),
        "total": round(sum(s["total_eur"] for s in summaries), 2),
        "count": len(summaries),
    }
    return {"companies": summaries, "totals": totals}


@router.post("/companies/{company_id}/subscription", status_code=201)
async def create_or_update_subscription(
    company_id: str,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Maak of update het abonnement voor een bedrijf.

    Body:
      - plan_slug: 'starter' | 'pro' | 'enterprise'
      - monthly_eur_override: optional float (admin only)
    """
    plan_slug = data.get("plan_slug")
    if not plan_slug:
        raise HTTPException(status_code=400, detail="plan_slug is verplicht")

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Bedrijf niet gevonden")

    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Abonnement '{plan_slug}' bestaat niet")

    sub_result = await db.execute(select(CompanySubscription).where(CompanySubscription.company_id == company.id))
    sub = sub_result.scalar_one_or_none()

    if sub:
        # Permission: only admin or the accountant owning this subscription can modify
        if current_user.role != "admin" and sub.accountant_id != current_user.id:
            raise HTTPException(status_code=403, detail="Geen toegang tot dit abonnement")
        sub.plan_id = plan.id
        if "monthly_eur_override" in data and current_user.role == "admin":
            sub.monthly_eur_override = data["monthly_eur_override"]
        sub.updated_at = datetime.utcnow()
    else:
        # New subscription
        if current_user.role not in ("admin", "accountant"):
            raise HTTPException(status_code=403, detail="Alleen admins en accountants mogen abonnementen aanmaken")
        sub = CompanySubscription(
            id=uuid.uuid4(),
            company_id=company.id,
            plan_id=plan.id,
            accountant_id=current_user.id if current_user.role == "accountant" else None,
            monthly_eur_override=data.get("monthly_eur_override") if current_user.role == "admin" else None,
            period_start=date.today(),
            ai_credits_used=0,
            ai_cost_eur_cents=0,
            status="active",
        )
        db.add(sub)

    await db.flush()
    return _subscription_summary(sub, plan, company)


@router.post("/ai-usage", status_code=201)
async def log_ai_usage(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log een AI gebruik event en increment de subscription counter.

    Body:
      - company_id (default: current_user.company_id)
      - operation: 'chat' | 'classify' | 'extract' | 'ocr'
      - model: optional
      - tokens_in / tokens_out
      - credits: aantal credits dat dit verbruikt (default 1)
      - cost_eur_cents: optional cost in cents
    """
    company_id = data.get("company_id") or (str(current_user.company_id) if current_user.company_id else None)
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is verplicht")

    operation = data.get("operation", "chat")
    credits = int(data.get("credits", 1))
    cost_cents = int(data.get("cost_eur_cents", 0))

    usage = AiUsage(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        user_id=current_user.id,
        operation=operation,
        model=data.get("model"),
        tokens_in=int(data.get("tokens_in", 0)),
        tokens_out=int(data.get("tokens_out", 0)),
        credits=credits,
        cost_eur_cents=cost_cents,
    )
    db.add(usage)

    # Increment subscription counter
    sub_result = await db.execute(select(CompanySubscription).where(CompanySubscription.company_id == uuid.UUID(company_id)))
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.ai_credits_used = (sub.ai_credits_used or 0) + credits
        sub.ai_cost_eur_cents = (sub.ai_cost_eur_cents or 0) + cost_cents
        sub.updated_at = datetime.utcnow()

    await db.flush()
    return {"id": str(usage.id), "credits": credits, "cost_eur_cents": cost_cents}


@router.post("/admin/seed-plans", status_code=201)
async def seed_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Idempotent: zorg dat de standaard plannen bestaan. Alleen admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen admins")

    defaults = [
        {"slug": "starter", "name": "Starter", "description": "Voor ZZP'ers en kleine ondernemers",
         "monthly_eur": 19.00, "ai_credits_included": 100, "ai_overage_eur_cents": 20, "max_users": 1, "sort_order": 1,
         "features": {"facturen": True, "bank": True, "btw": True, "ai_basic": True}},
        {"slug": "pro", "name": "Pro", "description": "Voor groeiende bedrijven met meerdere medewerkers",
         "monthly_eur": 49.00, "ai_credits_included": 500, "ai_overage_eur_cents": 10, "max_users": 5, "sort_order": 2,
         "features": {"facturen": True, "bank": True, "btw": True, "ai_basic": True, "ai_advanced": True, "rapportage": True, "uren": True}},
        {"slug": "enterprise", "name": "Enterprise", "description": "Voor accountantskantoren en grote organisaties",
         "monthly_eur": 149.00, "ai_credits_included": 2000, "ai_overage_eur_cents": 5, "max_users": 25, "sort_order": 3,
         "features": {"facturen": True, "bank": True, "btw": True, "ai_basic": True, "ai_advanced": True, "rapportage": True, "uren": True, "audit": True, "multi_company": True, "api_access": True}},
    ]

    created = []
    for d in defaults:
        existing = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == d["slug"]))
        if existing.scalar_one_or_none():
            continue
        plan = SubscriptionPlan(
            id=uuid.uuid4(),
            slug=d["slug"],
            name=d["name"],
            description=d["description"],
            monthly_eur=d["monthly_eur"],
            ai_credits_included=d["ai_credits_included"],
            ai_overage_eur_cents=d["ai_overage_eur_cents"],
            max_users=d["max_users"],
            features=d["features"],
            sort_order=d["sort_order"],
            is_active=True,
        )
        db.add(plan)
        created.append(d["slug"])

    await db.flush()
    return {"created": created, "message": f"{len(created)} plan(s) created"}


# ============================================================
#  STRIPE CHECKOUT + CUSTOMER PORTAL
# ============================================================
@router.post("/checkout-session")
async def create_checkout(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Maak een Stripe Checkout Session aan voor een bedrijf + plan.

    Body:
      - company_id: UUID of the company to subscribe
      - plan_slug: 'starter' | 'pro' | 'enterprise'
    """
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is niet geconfigureerd")

    company_id = data.get("company_id")
    plan_slug = data.get("plan_slug")
    if not company_id or not plan_slug:
        raise HTTPException(status_code=400, detail="company_id en plan_slug zijn verplicht")

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Bedrijf niet gevonden")

    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug))
    plan = plan_result.scalar_one_or_none()
    if not plan or not plan.stripe_price_id:
        raise HTTPException(status_code=400, detail=f"Plan '{plan_slug}' heeft geen Stripe price ID")

    # Permission: admin or accountant of this company
    sub_result = await db.execute(select(CompanySubscription).where(CompanySubscription.company_id == company.id))
    sub = sub_result.scalar_one_or_none()
    if current_user.role != "admin" and (not sub or sub.accountant_id != current_user.id):
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")

    try:
        customer = stripe_service.get_or_create_customer(
            email=current_user.email,
            name=company.name,
            company_id=str(company.id),
        )

        if sub and not sub.stripe_customer_id:
            sub.stripe_customer_id = customer.id
            await db.flush()

        session = stripe_service.create_checkout_session(
            customer_id=customer.id,
            price_id=plan.stripe_price_id,
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            company_id=str(company.id),
            plan_slug=plan_slug,
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        logger.exception("Stripe checkout failed")
        raise HTTPException(status_code=502, detail=f"Stripe fout: {str(e)[:200]}")


@router.post("/portal-session")
async def create_portal(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stripe Customer Portal voor abonnement-/betaalbeheer."""
    if not stripe_service.is_configured():
        raise HTTPException(status_code=503, detail="Stripe is niet geconfigureerd")

    company_id = data.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is verplicht")

    sub_result = await db.execute(select(CompanySubscription).where(CompanySubscription.company_id == company_id))
    sub = sub_result.scalar_one_or_none()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="Geen Stripe klant voor dit bedrijf")

    if current_user.role != "admin" and sub.accountant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Geen toegang")

    try:
        portal = stripe_service.create_portal_session(
            customer_id=sub.stripe_customer_id,
            return_url=settings.STRIPE_SUCCESS_URL,
        )
        return {"url": portal.url}
    except Exception as e:
        logger.exception("Stripe portal failed")
        raise HTTPException(status_code=502, detail=f"Stripe fout: {str(e)[:200]}")


# ============================================================
#  ADMIN OVERVIEW — Stripe payments / invoices / subscriptions
# ============================================================
@router.get("/payments")
async def list_payments(admin: User = Depends(require_admin)):
    """Lijst van alle Stripe payment intents (admin only)."""
    if not stripe_service.is_configured():
        return {"payments": [], "message": "Stripe niet geconfigureerd"}
    return {"payments": stripe_service.list_payments(limit=100)}


@router.get("/invoices")
async def list_stripe_invoices(admin: User = Depends(require_admin)):
    """Lijst van alle Stripe facturen (admin only)."""
    if not stripe_service.is_configured():
        return {"invoices": [], "message": "Stripe niet geconfigureerd"}
    return {"invoices": stripe_service.list_invoices(limit=100)}


@router.get("/subscriptions")
async def list_stripe_subscriptions(admin: User = Depends(require_admin)):
    """Lijst van alle Stripe subscriptions (admin only)."""
    if not stripe_service.is_configured():
        return {"subscriptions": [], "message": "Stripe niet geconfigureerd"}
    return {"subscriptions": stripe_service.list_subscriptions(limit=100)}


# ============================================================
#  STRIPE WEBHOOK
# ============================================================
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Verwerk Stripe events: subscription created/updated/deleted, invoice paid/failed."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_service.verify_webhook(payload, sig_header)
    except Exception as e:
        logger.warning(f"Stripe webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    obj = event["data"]["object"]
    logger.info(f"Stripe webhook: {event_type}")

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        company_id = obj.get("metadata", {}).get("company_id")
        if company_id:
            sub_result = await db.execute(
                select(CompanySubscription).where(CompanySubscription.company_id == company_id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                sub.stripe_subscription_id = obj["id"]
                sub.stripe_customer_id = obj["customer"]
                sub.status = obj["status"]
                sub.updated_at = datetime.utcnow()
                await db.flush()

    elif event_type == "customer.subscription.deleted":
        sub_result = await db.execute(
            select(CompanySubscription).where(CompanySubscription.stripe_subscription_id == obj["id"])
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.status = "cancelled"
            sub.updated_at = datetime.utcnow()
            await db.flush()

    elif event_type == "invoice.payment_succeeded":
        sub_id = obj.get("subscription")
        if sub_id:
            sub_result = await db.execute(
                select(CompanySubscription).where(CompanySubscription.stripe_subscription_id == sub_id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                sub.last_payment_at = datetime.utcnow()
                sub.status = "active"
                # Reset AI counters at start of new period
                sub.ai_credits_used = 0
                sub.ai_cost_eur_cents = 0
                sub.period_start = date.today()
                await db.flush()

    elif event_type == "invoice.payment_failed":
        sub_id = obj.get("subscription")
        if sub_id:
            sub_result = await db.execute(
                select(CompanySubscription).where(CompanySubscription.stripe_subscription_id == sub_id)
            )
            sub = sub_result.scalar_one_or_none()
            if sub:
                sub.status = "past_due"
                await db.flush()

    return {"received": True}
