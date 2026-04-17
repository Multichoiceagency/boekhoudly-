import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.database import init_db, async_session, engine
    from sqlalchemy import text
    import app.models  # noqa: ensure all models are imported
    await init_db()
    logger.info("FiscalFlow AI API gestart - database tables ready")

    # Lightweight idempotent migrations — add columns on existing tables
    migrations = [
        "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS stripe_product_id VARCHAR(255)",
        "ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS stripe_price_id VARCHAR(255)",
        "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255)",
        "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255)",
        "ALTER TABLE company_subscriptions ADD COLUMN IF NOT EXISTS last_payment_at TIMESTAMP",
        "CREATE INDEX IF NOT EXISTS ix_crm_lookup ON crm_records (provider, resource, external_id)",
        "CREATE INDEX IF NOT EXISTS ix_crm_company_resource ON crm_records (company_id, resource)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_company_provider ON integration_connections (company_id, provider)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual'",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS source_id VARCHAR(255)",
        "ALTER TABLE debtors ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual'",
        "ALTER TABLE debtors ADD COLUMN IF NOT EXISTS source_id VARCHAR(255)",
        "ALTER TABLE creditors ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual'",
        "ALTER TABLE creditors ADD COLUMN IF NOT EXISTS source_id VARCHAR(255)",
        "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual'",
        "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS source_id VARCHAR(255)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS document_type VARCHAR(20) DEFAULT 'factuur'",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS related_invoice_id VARCHAR(100)",
        "ALTER TABLE companies ALTER COLUMN logo_url TYPE TEXT",
    ]
    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                logger.warning(f"Migration skipped: {sql[:60]}... ({e})")

    # Seed default subscription plans + sync Stripe IDs from env
    try:
        from app.models.subscription_plan import SubscriptionPlan
        from app.config import get_settings
        from sqlalchemy import select
        import uuid

        s = get_settings()
        stripe_prices = {
            "starter": s.STRIPE_PRICE_STARTER,
            "pro": s.STRIPE_PRICE_PRO,
            "enterprise": s.STRIPE_PRICE_ENTERPRISE,
        }

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

        async with async_session() as session:
            for d in defaults:
                existing_result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == d["slug"]))
                existing = existing_result.scalar_one_or_none()
                stripe_price_id = stripe_prices.get(d["slug"], "")
                if existing:
                    # Always sync the latest Stripe price ID from env
                    if stripe_price_id and existing.stripe_price_id != stripe_price_id:
                        existing.stripe_price_id = stripe_price_id
                else:
                    session.add(SubscriptionPlan(
                        id=uuid.uuid4(),
                        is_active=True,
                        stripe_price_id=stripe_price_id or None,
                        **d,
                    ))
            await session.commit()
        logger.info("Default subscription plans seeded + Stripe IDs synced")
    except Exception as e:
        logger.warning(f"Could not seed plans: {e}")

    yield
    # Shutdown
    logger.info("FiscalFlow AI API gestopt")


app = FastAPI(
    title="FiscalFlow AI API",
    description="AI-powered boekhoudplatform voor Nederlandse ondernemers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, upload, transactions, vat, ai, bank, cloud_storage, perfex, admin, workspace, webhooks, kvk, billing, integrations, analyse, crm_import, uitstel, universal_import

app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(vat.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(bank.router, prefix="/api")
app.include_router(cloud_storage.router, prefix="/api")
app.include_router(perfex.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(kvk.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(analyse.router, prefix="/api")
app.include_router(crm_import.router, prefix="/api")
app.include_router(uitstel.router, prefix="/api")
app.include_router(universal_import.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FiscalFlow AI"}
