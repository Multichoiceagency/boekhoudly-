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
from sqlalchemy import select, delete
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.debtor import Debtor
from app.models.creditor import Creditor
from app.models.crm_cache import CrmRecord
from app.utils.auth import get_current_user
from app.api.workspace import _resolve_company_id

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
    """Import Perfex invoices with resolved client names and full detail."""
    if not admin.company_id:
        raise HTTPException(status_code=400, detail="Admin heeft geen bedrijf")

    # Build customer lookup table from cached customers
    cust_result = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "customers")
    )
    customer_names: dict[str, str] = {}
    for c in cust_result.scalars().all():
        cp = c.payload or {}
        cid = str(cp.get("userid") or c.external_id)
        customer_names[cid] = cp.get("company") or f"Klant {cid}"

    cached = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "invoices")
    )
    records = cached.scalars().all()

    status_map = {"1": "verzonden", "2": "betaald", "3": "verzonden", "4": "verlopen", "5": "concept", "6": "concept"}

    created, skipped, updated = 0, 0, 0
    for rec in records:
        p = rec.payload or {}
        ext_id = str(p.get("id") or rec.external_id)
        client_id = str(p.get("clientid") or "")
        client_name = customer_names.get(client_id, f"Klant {client_id}")

        # Build proper lines from subtotal + tax
        subtotal = _safe_float(p.get("subtotal"))
        total_tax = _safe_float(p.get("total_tax"))
        btw_rate = (total_tax / subtotal * 100) if subtotal > 0 else 21.0
        # Round to nearest standard rate
        if abs(btw_rate - 21) < 2:
            btw_rate = 21
        elif abs(btw_rate - 9) < 2:
            btw_rate = 9
        elif abs(btw_rate) < 1:
            btw_rate = 0

        client_note = p.get("clientnote") or ""
        admin_note = p.get("adminnote") or ""
        notes_parts = [n for n in [client_note, admin_note] if n and n.strip()]

        existing_result = await db.execute(
            select(Invoice).where(Invoice.company_id == admin.company_id, Invoice.source == "perfex", Invoice.source_id == ext_id)
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing with better data (resolve client names etc.)
            if existing.client != client_name and client_name != f"Klant {client_id}":
                existing.client = client_name
                existing.client_id = client_id
                updated += 1
            skipped += 1
            continue

        inv = Invoice(
            id=uuid.uuid4(),
            company_id=admin.company_id,
            number=p.get("formatted_number") or p.get("number") or f"PFX-{ext_id}",
            client=client_name,
            client_id=client_id,
            date=_safe_date(p.get("date")),
            due_date=_safe_date(p.get("duedate")),
            lines=[{
                "desc": f"Factuur {p.get('formatted_number') or ext_id}",
                "qty": 1,
                "price": round(subtotal, 2),
                "btwRate": btw_rate,
            }],
            status=status_map.get(str(p.get("status")), "concept"),
            notes="\n".join(notes_parts) if notes_parts else None,
            source="perfex",
            source_id=ext_id,
        )
        db.add(inv)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "updated": updated, "total_cached": len(records)}


@router.post("/perfex/estimates")
async def import_perfex_estimates(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import Perfex estimates as FiscaalFlow offertes (document_type='offerte')."""
    if not admin.company_id:
        raise HTTPException(status_code=400, detail="Admin heeft geen bedrijf")

    # Customer lookup
    cust_result = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "customers")
    )
    customer_names: dict[str, str] = {}
    for c in cust_result.scalars().all():
        cp = c.payload or {}
        customer_names[str(cp.get("userid") or c.external_id)] = cp.get("company") or ""

    cached = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "estimates")
    )
    records = cached.scalars().all()

    created, skipped = 0, 0
    for rec in records:
        p = rec.payload or {}
        ext_id = str(p.get("id") or rec.external_id)
        client_id = str(p.get("clientid") or "")

        existing = await db.execute(
            select(Invoice).where(Invoice.company_id == admin.company_id, Invoice.source == "perfex", Invoice.source_id == f"est-{ext_id}")
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        subtotal = _safe_float(p.get("subtotal"))
        total_tax = _safe_float(p.get("total_tax"))
        btw_rate = round((total_tax / subtotal * 100) if subtotal > 0 else 21)

        inv = Invoice(
            id=uuid.uuid4(),
            company_id=admin.company_id,
            document_type="offerte",
            number=p.get("formatted_number") or f"OFT-PFX-{ext_id}",
            client=customer_names.get(client_id, f"Klant {client_id}"),
            client_id=client_id,
            date=_safe_date(p.get("date")),
            due_date=_safe_date(p.get("expirydate")),
            lines=[{"desc": f"Offerte {ext_id}", "qty": 1, "price": round(subtotal, 2), "btwRate": btw_rate}],
            status="concept",
            source="perfex",
            source_id=f"est-{ext_id}",
        )
        db.add(inv)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "total_cached": len(records)}


@router.post("/perfex/credit-notes")
async def import_perfex_credit_notes(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import Perfex credit notes as FiscaalFlow creditnotas."""
    if not admin.company_id:
        raise HTTPException(status_code=400, detail="Admin heeft geen bedrijf")

    cust_result = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "customers")
    )
    customer_names: dict[str, str] = {}
    for c in cust_result.scalars().all():
        cp = c.payload or {}
        customer_names[str(cp.get("userid") or c.external_id)] = cp.get("company") or ""

    cached = await db.execute(
        select(CrmRecord).where(CrmRecord.provider == "perfex", CrmRecord.resource == "credit_notes")
    )
    records = cached.scalars().all()

    created, skipped = 0, 0
    for rec in records:
        p = rec.payload or {}
        ext_id = str(p.get("id") or rec.external_id)
        client_id = str(p.get("clientid") or "")

        existing = await db.execute(
            select(Invoice).where(Invoice.company_id == admin.company_id, Invoice.source == "perfex", Invoice.source_id == f"cn-{ext_id}")
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        subtotal = _safe_float(p.get("subtotal"))
        total_tax = _safe_float(p.get("total_tax"))

        inv = Invoice(
            id=uuid.uuid4(),
            company_id=admin.company_id,
            document_type="creditnota",
            number=p.get("formatted_number") or f"CN-PFX-{ext_id}",
            client=customer_names.get(client_id, f"Klant {client_id}"),
            client_id=client_id,
            date=_safe_date(p.get("date")),
            due_date=_safe_date(p.get("date")),
            lines=[{"desc": f"Creditnota {ext_id}", "qty": 1, "price": -round(subtotal, 2), "btwRate": 21}],
            status="concept",
            source="perfex",
            source_id=f"cn-{ext_id}",
        )
        db.add(inv)
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "total_cached": len(records)}


@router.delete("/perfex/clear")
async def clear_perfex_imports(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete ALL previously imported Perfex records so they can be re-imported fresh."""
    inv_del = await db.execute(delete(Invoice).where(Invoice.source == "perfex"))
    deb_del = await db.execute(delete(Debtor).where(Debtor.source == "perfex"))
    await db.flush()
    return {
        "deleted_invoices": inv_del.rowcount,
        "deleted_debtors": deb_del.rowcount,
    }


@router.post("/perfex/all")
async def import_perfex_all(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import ALL Perfex data: customers + invoices + estimates + credit notes."""
    customers = await import_perfex_customers(admin=admin, db=db)
    invoices = await import_perfex_invoices(admin=admin, db=db)
    estimates = await import_perfex_estimates(admin=admin, db=db)
    credit_notes = await import_perfex_credit_notes(admin=admin, db=db)
    return {
        "customers": customers,
        "invoices": invoices,
        "estimates": estimates,
        "credit_notes": credit_notes,
    }


@router.delete("/universal/{provider}/clear")
async def clear_universal_imports(
    provider: str,
    company_id: str | None = None,
    user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete previously imported records for this provider, scoped to the
    caller's selected company. Without a company filter a multi-tenant admin
    would wipe every customer's imports at once."""
    resolved = await _resolve_company_id(user, company_id, db)
    if not resolved:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")
    inv_del = await db.execute(
        delete(Invoice).where(Invoice.source == provider, Invoice.company_id == resolved)
    )
    deb_del = await db.execute(
        delete(Debtor).where(Debtor.source == provider, Debtor.company_id == resolved)
    )
    await db.flush()
    return {"provider": provider, "deleted_invoices": inv_del.rowcount, "deleted_debtors": deb_del.rowcount}
