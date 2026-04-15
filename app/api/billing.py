import uuid
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.subscription_plan import SubscriptionPlan
from app.models.company_subscription import CompanySubscription
from app.models.ai_usage import AiUsage
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


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
