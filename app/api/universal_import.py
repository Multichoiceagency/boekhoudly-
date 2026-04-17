"""Universal import pipeline — works for ANY connected provider.

Takes data from any IntegrationClient (Perfex, Moneybird, WeFact, Shopify,
WooCommerce, Magento, Medusa, etc.) and normalizes it into FiscaalFlow
native records: debtors, invoices, offertes, creditnotas.

The pipeline:
1. Loads the IntegrationConnection for the company+provider
2. Calls list_customers/list_invoices/list_payments via the client
3. Normalizes provider-specific fields to a common shape
4. Creates native Debtor/Invoice records with source={provider}
5. Idempotent: skips records that already exist by source+source_id
"""
import uuid
import logging
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.debtor import Debtor
from app.models.integration_connection import IntegrationConnection
from app.services.integrations import get_client
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["Universal Import"])


async def _require_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "accountant"):
        raise HTTPException(status_code=403, detail="Alleen admins en accountants")
    return current_user


def _safe_date(raw) -> date:
    if not raw:
        return date.today()
    try:
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw)[:10])
    except Exception:
        return date.today()


def _safe_float(raw) -> float:
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _guess_btw(subtotal: float, total: float) -> float:
    """Guess BTW rate from subtotal and total."""
    if subtotal <= 0:
        return 21
    tax = total - subtotal
    rate = (tax / subtotal) * 100
    if abs(rate - 21) < 3:
        return 21
    if abs(rate - 9) < 3:
        return 9
    if abs(rate) < 2:
        return 0
    return round(rate, 1)


# ============================================================
# Provider-specific normalizers
# ============================================================

def _normalize_customer(provider: str, raw: dict) -> dict:
    """Normalize a customer record from any provider to a common shape."""
    if provider == "perfex":
        return {
            "ext_id": str(raw.get("userid") or raw.get("id") or ""),
            "name": raw.get("company") or raw.get("name") or "",
            "email": (raw.get("email") or "").strip(),
            "address": raw.get("address") or raw.get("billing_street") or "",
            "city": (raw.get("city") or raw.get("billing_city") or "").strip(),
            "vat": raw.get("vat") or "",
        }
    if provider == "moneybird":
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": raw.get("company_name") or f"{raw.get('firstname', '')} {raw.get('lastname', '')}".strip(),
            "email": raw.get("email") or "",
            "address": raw.get("address1") or "",
            "city": raw.get("city") or "",
            "vat": raw.get("tax_number") or "",
        }
    if provider == "wefact":
        return {
            "ext_id": str(raw.get("Identifier") or raw.get("DebtorCode") or ""),
            "name": raw.get("CompanyName") or raw.get("Initials", "") + " " + raw.get("SurName", ""),
            "email": raw.get("EmailAddress") or "",
            "address": raw.get("Address") or "",
            "city": raw.get("City") or "",
            "vat": raw.get("TaxNumber") or "",
        }
    if provider in ("shopify", "woocommerce", "magento", "medusa"):
        billing = raw.get("billing") or raw.get("billing_address") or {}
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": f"{raw.get('first_name', '') or billing.get('first_name', '')} {raw.get('last_name', '') or billing.get('last_name', '')}".strip() or raw.get("email") or "",
            "email": raw.get("email") or "",
            "address": billing.get("address1") or billing.get("address_1") or billing.get("street") or "",
            "city": billing.get("city") or "",
            "vat": "",
        }
    # Generic fallback
    return {
        "ext_id": str(raw.get("id") or ""),
        "name": raw.get("name") or raw.get("company") or raw.get("email") or "",
        "email": raw.get("email") or "",
        "address": raw.get("address") or "",
        "city": raw.get("city") or "",
        "vat": raw.get("vat") or raw.get("tax_number") or "",
    }


def _normalize_invoice(provider: str, raw: dict, customer_names: dict) -> dict:
    """Normalize an invoice/order from any provider to a common shape."""
    if provider == "perfex":
        client_id = str(raw.get("clientid") or "")
        subtotal = _safe_float(raw.get("subtotal"))
        total_tax = _safe_float(raw.get("total_tax"))
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("formatted_number") or raw.get("number") or "",
            "client": customer_names.get(client_id, f"Klant {client_id}"),
            "client_id": client_id,
            "date": raw.get("date"),
            "due_date": raw.get("duedate"),
            "subtotal": subtotal,
            "btw_rate": _guess_btw(subtotal, subtotal + total_tax),
            "status": {"1": "verzonden", "2": "betaald", "3": "verzonden", "4": "verlopen", "5": "concept"}.get(str(raw.get("status")), "concept"),
            "notes": raw.get("clientnote") or raw.get("adminnote") or "",
        }
    if provider == "moneybird":
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("invoice_id") or "",
            "client": raw.get("contact", {}).get("company_name") or customer_names.get(str(raw.get("contact_id")), ""),
            "client_id": str(raw.get("contact_id") or ""),
            "date": raw.get("invoice_date"),
            "due_date": raw.get("due_date"),
            "subtotal": _safe_float(raw.get("total_price_excl_tax")),
            "btw_rate": 21,
            "status": {"open": "verzonden", "late": "verlopen", "paid": "betaald", "draft": "concept"}.get(raw.get("state", ""), "concept"),
            "notes": raw.get("reference") or "",
        }
    if provider == "wefact":
        return {
            "ext_id": str(raw.get("Identifier") or raw.get("InvoiceCode") or ""),
            "number": raw.get("InvoiceCode") or "",
            "client": customer_names.get(str(raw.get("DebtorCode")), raw.get("CompanyName") or ""),
            "client_id": str(raw.get("DebtorCode") or ""),
            "date": raw.get("Date"),
            "due_date": raw.get("DueDate"),
            "subtotal": _safe_float(raw.get("AmountExcl")),
            "btw_rate": _guess_btw(_safe_float(raw.get("AmountExcl")), _safe_float(raw.get("AmountIncl"))),
            "status": {"0": "concept", "1": "verzonden", "2": "betaald", "3": "verlopen"}.get(str(raw.get("Status")), "concept"),
            "notes": "",
        }
    if provider in ("shopify", "woocommerce"):
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": str(raw.get("order_number") or raw.get("number") or raw.get("name") or ""),
            "client": f"{raw.get('billing', {}).get('first_name', '')} {raw.get('billing', {}).get('last_name', '')}".strip() or raw.get("email") or "",
            "client_id": str(raw.get("customer_id") or raw.get("customer", {}).get("id") or ""),
            "date": (raw.get("created_at") or raw.get("date_created") or "")[:10],
            "due_date": None,
            "subtotal": _safe_float(raw.get("total") or raw.get("total_price")),
            "btw_rate": _safe_float(raw.get("total_tax", 0)) / max(_safe_float(raw.get("total") or raw.get("total_price") or 1), 0.01) * 100,
            "status": {"paid": "betaald", "completed": "betaald", "processing": "verzonden", "pending": "concept", "refunded": "concept"}.get(raw.get("status") or raw.get("financial_status", ""), "concept"),
            "notes": raw.get("note") or "",
        }
    if provider in ("magento", "medusa"):
        return {
            "ext_id": str(raw.get("entity_id") or raw.get("id") or ""),
            "number": str(raw.get("increment_id") or raw.get("display_id") or ""),
            "client": raw.get("customer_firstname", "") + " " + raw.get("customer_lastname", "") if raw.get("customer_firstname") else customer_names.get(str(raw.get("customer_id")), ""),
            "client_id": str(raw.get("customer_id") or ""),
            "date": (raw.get("created_at") or "")[:10],
            "due_date": None,
            "subtotal": _safe_float(raw.get("grand_total") or raw.get("total")),
            "btw_rate": 21,
            "status": "betaald" if raw.get("status") in ("complete", "captured") else "concept",
            "notes": "",
        }
    # Generic fallback
    return {
        "ext_id": str(raw.get("id") or ""),
        "number": str(raw.get("number") or raw.get("invoice_number") or ""),
        "client": raw.get("name") or raw.get("customer_name") or "",
        "client_id": str(raw.get("customer_id") or ""),
        "date": raw.get("date") or raw.get("created_at"),
        "due_date": raw.get("due_date"),
        "subtotal": _safe_float(raw.get("total") or raw.get("amount")),
        "btw_rate": 21,
        "status": "concept",
        "notes": "",
    }


# ============================================================
# Universal import endpoint
# ============================================================

@router.post("/universal/{provider}")
async def universal_import(
    provider: str,
    user: User = Depends(_require_manager),
    db: AsyncSession = Depends(get_db),
):
    """Universal import: fetch data from any connected provider and create native records.

    Works for: perfex, moneybird, wefact, shopify, woocommerce, magento, medusa, snelstart, etc.

    Pipeline:
    1. Load IntegrationConnection credentials from DB
    2. Call list_customers + list_invoices via the provider client
    3. Normalize to common shape
    4. Create Debtor + Invoice records with source={provider}
    5. Skip existing (idempotent by source+source_id)
    """
    # Find the connection for this provider + company
    company_id = user.company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")

    conn_result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider == provider,
        )
    )
    conn = conn_result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail=f"Geen {provider} koppeling gevonden voor dit bedrijf")

    try:
        client = get_client(provider, conn.credentials)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = {"customers": {"created": 0, "skipped": 0}, "invoices": {"created": 0, "skipped": 0}}

    # --- Import customers → Debtors ---
    try:
        raw_customers = await client.list_customers()
        customer_names: dict[str, str] = {}

        for raw in raw_customers:
            norm = _normalize_customer(provider, raw)
            if not norm["ext_id"]:
                continue
            customer_names[norm["ext_id"]] = norm["name"]

            existing = await db.execute(
                select(Debtor).where(Debtor.company_id == company_id, Debtor.source == provider, Debtor.source_id == norm["ext_id"])
            )
            if existing.scalar_one_or_none():
                results["customers"]["skipped"] += 1
                continue

            db.add(Debtor(
                id=uuid.uuid4(),
                company_id=company_id,
                name=norm["name"] or f"Klant {norm['ext_id']}",
                email=norm["email"] or None,
                btw=norm["vat"] or None,
                address=norm["address"] or None,
                city=norm["city"] or None,
                payment_term=30,
                source=provider,
                source_id=norm["ext_id"],
            ))
            results["customers"]["created"] += 1

        logger.info(f"Universal import {provider}: {results['customers']['created']} customers created")
    except NotImplementedError:
        results["customers"]["error"] = "Niet ondersteund voor deze provider"
    except Exception as e:
        results["customers"]["error"] = str(e)[:200]
        logger.warning(f"Universal import {provider} customers failed: {e}")

    # --- Import invoices/orders → Invoices ---
    try:
        raw_invoices = await client.list_invoices()

        for raw in raw_invoices:
            norm = _normalize_invoice(provider, raw, customer_names)
            if not norm["ext_id"]:
                continue

            existing = await db.execute(
                select(Invoice).where(Invoice.company_id == company_id, Invoice.source == provider, Invoice.source_id == norm["ext_id"])
            )
            if existing.scalar_one_or_none():
                results["invoices"]["skipped"] += 1
                continue

            btw_rate = norm["btw_rate"]
            if abs(btw_rate - 21) < 3:
                btw_rate = 21
            elif abs(btw_rate - 9) < 3:
                btw_rate = 9
            elif abs(btw_rate) < 2:
                btw_rate = 0

            db.add(Invoice(
                id=uuid.uuid4(),
                company_id=company_id,
                number=norm["number"] or f"{provider.upper()}-{norm['ext_id']}",
                client=norm["client"] or f"Klant {norm['client_id']}",
                client_id=norm["client_id"],
                date=_safe_date(norm["date"]),
                due_date=_safe_date(norm["due_date"]),
                lines=[{
                    "desc": f"{norm['number'] or provider}",
                    "qty": 1,
                    "price": round(norm["subtotal"], 2),
                    "btwRate": btw_rate,
                }],
                status=norm["status"],
                notes=norm["notes"] or None,
                source=provider,
                source_id=norm["ext_id"],
            ))
            results["invoices"]["created"] += 1

        logger.info(f"Universal import {provider}: {results['invoices']['created']} invoices created")
    except NotImplementedError:
        results["invoices"]["error"] = "Niet ondersteund voor deze provider"
    except Exception as e:
        results["invoices"]["error"] = str(e)[:200]
        logger.warning(f"Universal import {provider} invoices failed: {e}")

    await db.flush()

    # Update connection metadata
    conn.last_sync_at = datetime.utcnow()
    conn.metadata_json = {
        **(conn.metadata_json or {}),
        "last_import": {
            "customers_created": results["customers"].get("created", 0),
            "invoices_created": results["invoices"].get("created", 0),
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await db.flush()

    return {"provider": provider, "results": results}
