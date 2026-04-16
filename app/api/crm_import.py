"""Import cached CRM records into FiscaalFlow native tables.

Converts Perfex (and later Moneybird/WeFact) customers → debtors,
invoices → invoices, etc. Each imported record gets source='perfex'
and source_id=external_id for traceability. Idempotent: existing
records with the same source+source_id are skipped.
"""
import uuid
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.debtor import Debtor
from app.models.creditor import Creditor
from app.models.crm_cache import CrmRecord
from app.utils.auth import get_current_user

router = APIRouter(prefix="/import", tags=["Import"])


async def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "accountant"):
        raise HTTPException(status_code=403, detail="Alleen admins en accountants hebben toegang")
    return current_user


def _safe_date(raw) -> date:
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(str(raw)[:10])
    except Exception:
        return date.today()


def _safe_float(raw) -> float:
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


@router.post("/perfex/customers")
async def import_perfex_customers(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import Perfex customers as FiscaalFlow debtors."""
    if not admin.company_id:
        raise HTTPException(status_code=400, detail="Admin heeft geen bedrijf")

    cached = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "customers")
    )
    records = cached.scalars().all()

    created, skipped = 0, 0
    for rec in records:
        p = rec.payload or {}
        ext_id = str(p.get("userid") or rec.external_id)

        existing = await db.execute(
            select(Debtor).where(Debtor.company_id == admin.company_id, Debtor.source == "perfex", Debtor.source_id == ext_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        debtor = Debtor(
            id=uuid.uuid4(),
            company_id=admin.company_id,
            name=p.get("company") or f"Klant {ext_id}",
            email=(p.get("email") or "").strip() or None,
            kvk=None,
            btw=p.get("vat") or None,
            address=p.get("address") or None,
            city=(p.get("city") or "").strip() or None,
            iban=None,
            payment_term=30,
            source="perfex",
            source_id=ext_id,
        )
        db.add(debtor)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "total_cached": len(records)}


@router.post("/perfex/invoices")
async def import_perfex_invoices(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import Perfex invoices as FiscaalFlow invoices."""
    if not admin.company_id:
        raise HTTPException(status_code=400, detail="Admin heeft geen bedrijf")

    cached = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "invoices")
    )
    records = cached.scalars().all()

    status_map = {"1": "verzonden", "2": "betaald", "3": "verzonden", "4": "verlopen", "5": "concept", "6": "concept"}

    created, skipped = 0, 0
    for rec in records:
        p = rec.payload or {}
        ext_id = str(p.get("id") or rec.external_id)

        existing = await db.execute(
            select(Invoice).where(Invoice.company_id == admin.company_id, Invoice.source == "perfex", Invoice.source_id == ext_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        inv = Invoice(
            id=uuid.uuid4(),
            company_id=admin.company_id,
            number=p.get("formatted_number") or p.get("number") or f"PFX-{ext_id}",
            client=str(p.get("clientid") or "Onbekend"),
            client_id=str(p.get("clientid") or ""),
            date=_safe_date(p.get("date")),
            due_date=_safe_date(p.get("duedate")),
            lines=[{
                "desc": "Geïmporteerd uit Perfex CRM",
                "qty": 1,
                "price": _safe_float(p.get("subtotal")),
                "btwRate": _safe_float(p.get("total_tax")) / max(_safe_float(p.get("subtotal")), 0.01) * 100 if _safe_float(p.get("subtotal")) > 0 else 21,
            }],
            status=status_map.get(str(p.get("status")), "concept"),
            notes=f"Geïmporteerd uit Perfex CRM (ID: {ext_id})",
            source="perfex",
            source_id=ext_id,
        )
        db.add(inv)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "total_cached": len(records)}


@router.post("/perfex/all")
async def import_perfex_all(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import all Perfex data (customers + invoices) into native tables."""
    customers = await import_perfex_customers(admin=admin, db=db)
    invoices = await import_perfex_invoices(admin=admin, db=db)
    return {
        "customers": customers,
        "invoices": invoices,
    }
