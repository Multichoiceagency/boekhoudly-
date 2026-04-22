"""Perfex CRM proxy + cache endpoints. Admin-only.

Credentials are loaded from integration_connections (per-company) first,
with PERFEX_CRM_URL/PERFEX_CRM_API_KEY env vars as backward-compat fallback.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.crm_cache import CrmRecord, CrmSyncRun
from app.models.integration_connection import IntegrationConnection
from app.services.perfex_service import PerfexCRMClient
from app.config import get_settings
from app.api.workspace import _resolve_company_id

router = APIRouter(prefix="/perfex", tags=["Perfex CRM"])
settings = get_settings()
PROVIDER = "perfex"


async def _resolve_credentials(
    user: User,
    db: AsyncSession,
    target_company_id: uuid.UUID | None = None,
) -> tuple[str, str] | None:
    """Find Perfex credentials: per-company DB first, then env-var fallback.

    `target_company_id` overrides `user.company_id` so accountants switching
    between client companies can sync the right Perfex install.
    """
    company_id = target_company_id or user.company_id
    if company_id:
        result = await db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.company_id == company_id,
                IntegrationConnection.provider == PROVIDER,
            )
        )
        conn = result.scalar_one_or_none()
        if conn and conn.credentials.get("url") and conn.credentials.get("api_key"):
            return conn.credentials["url"], conn.credentials["api_key"]
    if settings.PERFEX_CRM_URL and settings.PERFEX_CRM_API_KEY:
        return settings.PERFEX_CRM_URL, settings.PERFEX_CRM_API_KEY
    return None


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "accountant"):
        raise HTTPException(status_code=403, detail="Alleen admins en accountants hebben toegang")
    return current_user


def _client(url: str | None = None, api_key: str | None = None) -> PerfexCRMClient:
    """Build a Perfex client from explicit args (used by POST /test).
    For normal calls use _client_for_user instead."""
    try:
        return PerfexCRMClient(base_url=url, api_key=api_key)
    except ValueError:
        raise HTTPException(status_code=503, detail="Perfex CRM is niet geconfigureerd")


async def _client_for_user(
    user: User,
    db: AsyncSession,
    target_company_id: uuid.UUID | None = None,
) -> PerfexCRMClient:
    creds = await _resolve_credentials(user, db, target_company_id)
    if not creds:
        raise HTTPException(
            status_code=503,
            detail="Geen Perfex koppeling gevonden voor dit bedrijf. Voeg er een toe via Instellingen → Integraties.",
        )
    url, api_key = creds
    return PerfexCRMClient(base_url=url, api_key=api_key)


@router.get("/test")
async def test_connection_get(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Test the Perfex connection for the current user's company."""
    client = await _client_for_user(admin, db)
    return await client.test_connection()


@router.post("/test")
async def test_connection_post(data: dict, current_user: User = Depends(get_current_user)):
    """Test a custom Perfex CRM URL + API key (used in connect modal)."""
    url = data.get("url", "").strip()
    api_key = data.get("api_key", "").strip()
    if not url or not api_key:
        raise HTTPException(status_code=400, detail="URL en API key zijn verplicht")
    try:
        client = PerfexCRMClient(base_url=url, api_key=api_key)
        return await client.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}


@router.get("/ping")
async def ping_perfex(
    company_id: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Diagnostic: time each layer (DNS → TCP → TLS → HTTP) from inside
    this container to the configured Perfex host. Helps tell apart a
    "Perfex is slow" problem from a "Coolify network is slow" problem.

    Run via: GET /perfex/ping?company_id=<uuid>
    Returns JSON with timings in ms per step + the final HTTP response
    snapshot.
    """
    import asyncio, socket, ssl, time, urllib.parse
    from app.api.workspace import _resolve_company_id

    resolved = await _resolve_company_id(admin, company_id, db)
    creds = await _resolve_credentials(admin, db, resolved)
    if not creds:
        raise HTTPException(status_code=404, detail="Geen Perfex koppeling")
    url, api_key = creds
    parsed = urllib.parse.urlparse(url if url.startswith("http") else f"https://{url}")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    timings: dict = {"host": host, "port": port, "scheme": parsed.scheme}

    # 1. DNS
    t0 = time.perf_counter()
    try:
        addrs = await asyncio.get_event_loop().getaddrinfo(host, port)
        timings["dns_ms"] = int((time.perf_counter() - t0) * 1000)
        timings["resolved"] = [a[4][0] for a in addrs[:5]]
    except Exception as e:
        timings["dns_error"] = str(e) or type(e).__name__
        return timings

    # 2. Raw TCP connect (IPv4 only, matching our PerfexCRMClient transport)
    ipv4 = next((a[4] for a in addrs if a[0] == socket.AF_INET), None)
    if ipv4:
        t0 = time.perf_counter()
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(ipv4[0], port), timeout=10)
            timings["tcp_connect_ms"] = int((time.perf_counter() - t0) * 1000)
            w.close()
            try: await w.wait_closed()
            except Exception: pass
        except Exception as e:
            timings["tcp_error"] = f"{type(e).__name__}: {str(e) or ''}"
            return timings

    # 3. Full HTTP GET via our PerfexCRMClient so the transport config is identical
    from app.services.perfex_service import PerfexCRMClient
    try:
        client = PerfexCRMClient(base_url=url, api_key=api_key)
        t0 = time.perf_counter()
        data = await client._get("customers/search/a", timeout=30)
        timings["http_ttlb_ms"] = int((time.perf_counter() - t0) * 1000)
        timings["http_ok"] = True
        if isinstance(data, list):
            timings["http_rows"] = len(data)
    except Exception as e:
        timings["http_ok"] = False
        timings["http_error"] = f"{type(e).__name__}: {str(e) or ''}"

    return timings


@router.get("/summary")
async def summary(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Compact dashboard summary — counts of customers, invoices, payments,
    plus revenue totals from the invoices feed."""
    client = await _client_for_user(admin, db)
    customers = await client.get_customers()
    invoices = await client.get_invoices()
    payments = await client.get_payments()
    estimates = await client.get_estimates()

    total_revenue = 0.0
    paid_invoices = 0
    open_invoices = 0
    for inv in invoices:
        try:
            total = float(inv.get("total") or 0)
        except Exception:
            total = 0
        # Perfex invoice status: 1=unpaid, 2=paid, 3=partially paid, 4=overdue, 5=cancelled
        status = str(inv.get("status") or "")
        if status == "2":
            total_revenue += total
            paid_invoices += 1
        elif status in ("1", "3", "4"):
            open_invoices += 1

    return {
        "customers": len(customers),
        "invoices_total": len(invoices),
        "invoices_paid": paid_invoices,
        "invoices_open": open_invoices,
        "payments": len(payments),
        "estimates": len(estimates),
        "revenue_paid": round(total_revenue, 2),
    }


@router.get("/customers")
async def list_customers(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_customers()


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    customer = await client.get_customer(customer_id)
    contacts = await client.get_customer_contacts(customer_id)
    return {"customer": customer, "contacts": contacts}


@router.get("/invoices")
async def list_invoices(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_invoices()


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_invoice(invoice_id)


@router.get("/payments")
async def list_payments(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_payments()


@router.get("/estimates")
async def list_estimates(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_estimates()


@router.get("/proposals")
async def list_proposals(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_proposals()


@router.get("/credit-notes")
async def list_credit_notes(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_credit_notes()


@router.get("/leads")
async def list_leads(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_leads()


@router.get("/projects")
async def list_projects(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_projects()


@router.get("/items")
async def list_items(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    client = await _client_for_user(admin, db)
    return await client.get_items()


@router.get("/sync")
async def sync_all(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Fetch all key resources at once (no DB write — used by sync-to-db)."""
    client = await _client_for_user(admin, db)
    result = await client.sync_all()
    return {"counts": {k: len(v) for k, v in result.items()}, "data": result}


@router.post("/sync-to-db")
async def sync_to_db(
    company_id: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pull all resources from Perfex and persist them in crm_records.

    Scoped to the caller's selected company (?company_id=...) so sub-companies
    of an accountant keep their own caches. Only deletes + re-inserts rows
    for that company.
    """
    resolved = await _resolve_company_id(admin, company_id, db)
    if not resolved:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")

    run = CrmSyncRun(
        id=uuid.uuid4(),
        company_id=resolved,
        provider=PROVIDER,
        status="running",
    )
    db.add(run)
    await db.flush()

    try:
        client = await _client_for_user(admin, db, resolved)
        data = await client.sync_all()
    except HTTPException:
        run.status = "error"
        run.error = "Geen Perfex koppeling geconfigureerd"
        run.finished_at = datetime.utcnow()
        await db.flush()
        raise
    except Exception as e:
        run.status = "error"
        run.error = str(e)[:1900]
        run.finished_at = datetime.utcnow()
        await db.flush()
        raise HTTPException(status_code=502, detail=f"Perfex sync mislukt: {str(e)[:200]}")

    counts: dict = {}
    id_field = {
        "customers": "userid",
        "invoices": "id",
        "payments": "id",
        "estimates": "id",
        "proposals": "id",
        "credit_notes": "id",
        "subscriptions": "id",
        "leads": "id",
        "projects": "id",
        "items": "itemid",
        "tickets": "ticketid",
        "contracts": "id",
    }

    for resource, items in data.items():
        if not isinstance(items, list):
            continue
        await db.execute(
            delete(CrmRecord).where(
                CrmRecord.provider == PROVIDER,
                CrmRecord.resource == resource,
                CrmRecord.company_id == resolved,
            )
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            ext = str(item.get(id_field.get(resource, "id"), ""))
            if not ext:
                continue
            db.add(CrmRecord(
                id=uuid.uuid4(),
                company_id=resolved,
                provider=PROVIDER,
                resource=resource,
                external_id=ext,
                payload=item,
                synced_at=datetime.utcnow(),
            ))
        counts[resource] = len(items)

    run.status = "success"
    run.finished_at = datetime.utcnow()
    run.counts = counts
    await db.flush()

    return {"status": "success", "counts": counts, "run_id": str(run.id), "synced_at": run.finished_at.isoformat()}


@router.get("/sync-status")
async def sync_status(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent sync run for Perfex."""
    result = await db.execute(
        select(CrmSyncRun).where(CrmSyncRun.provider == PROVIDER).order_by(CrmSyncRun.started_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        return {"last_synced": None, "status": None, "counts": {}}
    return {
        "last_synced": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "counts": run.counts or {},
        "error": run.error,
    }


@router.delete("/clear-cache")
async def clear_cache(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Wis alle gecachete Perfex data + sync runs."""
    await db.execute(delete(CrmRecord).where(CrmRecord.provider == PROVIDER))
    await db.execute(delete(CrmSyncRun).where(CrmSyncRun.provider == PROVIDER))
    await db.flush()
    return {"status": "cleared", "provider": PROVIDER}


@router.get("/cached/{resource}")
async def get_cached(
    resource: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Read cached records for a resource (customers/invoices/payments/...)."""
    result = await db.execute(
        select(CrmRecord)
        .where(CrmRecord.provider == PROVIDER, CrmRecord.resource == resource)
        .order_by(CrmRecord.synced_at.desc())
    )
    records = result.scalars().all()
    return [r.payload for r in records]
