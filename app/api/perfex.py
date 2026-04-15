"""Perfex CRM proxy endpoints. Auth is shared across all clients via env vars
(PERFEX_CRM_URL + PERFEX_CRM_API_KEY) — only admins can hit these endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.perfex_service import PerfexCRMClient
from app.config import get_settings

router = APIRouter(prefix="/perfex", tags=["Perfex CRM"])
settings = get_settings()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen admins hebben toegang")
    return current_user


def _client(url: str | None = None, api_key: str | None = None) -> PerfexCRMClient:
    """Build a Perfex client. Falls back to env vars if URL/key not given."""
    try:
        return PerfexCRMClient(base_url=url, api_key=api_key)
    except ValueError:
        raise HTTPException(status_code=503, detail="Perfex CRM is niet geconfigureerd (PERFEX_CRM_URL + PERFEX_CRM_API_KEY ontbreken)")


@router.get("/test")
async def test_connection_get(admin: User = Depends(require_admin)):
    """Test the configured Perfex CRM connection."""
    client = _client()
    return await client.test_connection()


@router.post("/test")
async def test_connection_post(data: dict, current_user: User = Depends(get_current_user)):
    """Test a custom Perfex CRM URL + API key (used in settings UI)."""
    url = data.get("url", "").strip()
    api_key = data.get("api_key", "").strip()
    if not url or not api_key:
        raise HTTPException(status_code=400, detail="URL en API key zijn verplicht")
    try:
        client = PerfexCRMClient(base_url=url, api_key=api_key)
        return await client.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}


@router.get("/summary")
async def summary(admin: User = Depends(require_admin)):
    """Compact dashboard summary — counts of customers, invoices, payments,
    plus revenue totals from the invoices feed."""
    client = _client()
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
async def list_customers(admin: User = Depends(require_admin)):
    return await _client().get_customers()


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, admin: User = Depends(require_admin)):
    client = _client()
    customer = await client.get_customer(customer_id)
    contacts = await client.get_customer_contacts(customer_id)
    return {"customer": customer, "contacts": contacts}


@router.get("/invoices")
async def list_invoices(admin: User = Depends(require_admin)):
    return await _client().get_invoices()


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, admin: User = Depends(require_admin)):
    return await _client().get_invoice(invoice_id)


@router.get("/payments")
async def list_payments(admin: User = Depends(require_admin)):
    return await _client().get_payments()


@router.get("/estimates")
async def list_estimates(admin: User = Depends(require_admin)):
    return await _client().get_estimates()


@router.get("/proposals")
async def list_proposals(admin: User = Depends(require_admin)):
    return await _client().get_proposals()


@router.get("/credit-notes")
async def list_credit_notes(admin: User = Depends(require_admin)):
    return await _client().get_credit_notes()


@router.get("/leads")
async def list_leads(admin: User = Depends(require_admin)):
    return await _client().get_leads()


@router.get("/projects")
async def list_projects(admin: User = Depends(require_admin)):
    return await _client().get_projects()


@router.get("/items")
async def list_items(admin: User = Depends(require_admin)):
    return await _client().get_items()


@router.get("/sync")
async def sync_all(admin: User = Depends(require_admin)):
    """Fetch all key resources at once for an import overview."""
    client = _client()
    result = await client.sync_all()
    return {
        "counts": {k: len(v) for k, v in result.items()},
        "data": result,
    }
