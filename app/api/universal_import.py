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
from app.api.workspace import _resolve_company_id

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
    """Normalize a customer record from any provider to a common shape.
    Field names verified against official API documentation per provider."""

    if provider == "perfex":
        # Themesic REST API customer fields:
        # userid, company, vat, phonenumber, website, country, city, zip,
        # state, address, default_language, default_currency, longitude,
        # latitude, stripe_id, billing_* , shipping_*, datecreated.
        #
        # We promote the most-used ones to Debtor columns and stash the
        # richer Perfex-specific bits in `extra` so nothing is lost.
        billing_address = " ".join(
            str(raw.get(k) or "").strip() for k in ("billing_street", "billing_city", "billing_zip") if raw.get(k)
        ).strip()
        extra = {k: raw.get(k) for k in (
            "default_language", "default_currency", "stripe_id",
            "longitude", "latitude", "groups_in", "partnership_type",
            "billing_street", "billing_city", "billing_state", "billing_zip", "billing_country",
            "shipping_street", "shipping_city", "shipping_state", "shipping_zip", "shipping_country",
            "datecreated", "active", "leadid", "show_primary_contact",
        ) if raw.get(k) not in (None, "")}
        return {
            "ext_id": str(raw.get("userid") or raw.get("id") or ""),
            "name": raw.get("company") or raw.get("name") or "",
            "email": (raw.get("email") or "").strip(),
            "address": raw.get("address") or raw.get("billing_street") or billing_address or "",
            "city": (raw.get("city") or raw.get("billing_city") or "").strip(),
            "vat": raw.get("vat") or "",
            "kvk": "",
            "phone": raw.get("phonenumber") or "",
            "zip": raw.get("zip") or raw.get("billing_zip") or "",
            "state": raw.get("state") or raw.get("billing_state") or "",
            "country": raw.get("country") or raw.get("billing_country") or "",
            "website": raw.get("website") or "",
            "extra": extra or None,
        }
    if provider == "moneybird":
        # Moneybird v2: firstname (no underscore!), company_name, tax_number, address1, zipcode
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": raw.get("company_name") or f"{raw.get('firstname', '')} {raw.get('lastname', '')}".strip(),
            "email": raw.get("email") or "",
            "address": raw.get("address1") or "",
            "city": raw.get("city") or "",
            "vat": raw.get("tax_number") or "",
            "kvk": raw.get("chamber_of_commerce") or "",
            "phone": raw.get("phone") or "",
            "zip": raw.get("zipcode") or "",
        }
    if provider == "wefact":
        # WeFact: CompanyName, Initials, SurName, EmailAddress, Address, City, TaxNumber
        return {
            "ext_id": str(raw.get("Identifier") or raw.get("DebtorCode") or ""),
            "name": raw.get("CompanyName") or f"{raw.get('Initials', '')} {raw.get('SurName', '')}".strip(),
            "email": raw.get("EmailAddress") or "",
            "address": raw.get("Address") or "",
            "city": raw.get("City") or "",
            "vat": raw.get("TaxNumber") or "",
            "kvk": raw.get("CocNumber") or "",
            "phone": raw.get("PhoneNumber") or "",
            "zip": raw.get("ZipCode") or "",
        }
    if provider == "snelstart":
        # SnelStart B2B: naam, email, vestigingsAdres {straat, postcode, plaats}
        adres = raw.get("vestigingsAdres") or raw.get("correspondentieAdres") or {}
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": raw.get("naam") or "",
            "email": raw.get("email") or "",
            "address": adres.get("straat") or "",
            "city": adres.get("plaats") or "",
            "vat": raw.get("btwNummer") or "",
            "kvk": raw.get("kvkNummer") or "",
            "phone": raw.get("telefoon") or "",
            "zip": adres.get("postcode") or "",
        }
    if provider == "shopify":
        # Shopify Admin 2024-01: first_name, last_name, email, addresses[]
        addr = (raw.get("addresses") or [{}])[0] if raw.get("addresses") else (raw.get("default_address") or {})
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip() or raw.get("email") or "",
            "email": raw.get("email") or "",
            "address": addr.get("address1") or "",
            "city": addr.get("city") or "",
            "vat": "",
            "kvk": "",
            "phone": raw.get("phone") or addr.get("phone") or "",
            "zip": addr.get("zip") or "",
        }
    if provider == "woocommerce":
        # WooCommerce v3: billing.first_name, billing.last_name, billing.address_1, billing.city
        billing = raw.get("billing") or {}
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": f"{billing.get('first_name', '') or raw.get('first_name', '')} {billing.get('last_name', '') or raw.get('last_name', '')}".strip() or raw.get("email") or "",
            "email": raw.get("email") or billing.get("email") or "",
            "address": billing.get("address_1") or "",
            "city": billing.get("city") or "",
            "vat": "",
            "kvk": "",
            "phone": billing.get("phone") or "",
            "zip": billing.get("postcode") or "",
        }
    if provider == "magento":
        # Magento REST V1: firstname, lastname, email, addresses[].street[], city, postcode
        addrs = raw.get("addresses") or []
        addr = addrs[0] if addrs else {}
        street = addr.get("street") or []
        return {
            "ext_id": str(raw.get("id") or raw.get("entity_id") or ""),
            "name": f"{raw.get('firstname', '')} {raw.get('lastname', '')}".strip(),
            "email": raw.get("email") or "",
            "address": street[0] if isinstance(street, list) and street else str(street),
            "city": addr.get("city") or "",
            "vat": raw.get("taxvat") or "",
            "kvk": "",
            "phone": addr.get("telephone") or "",
            "zip": addr.get("postcode") or "",
        }
    if provider == "medusa":
        # Medusa Admin: first_name, last_name, email, shipping_addresses[]
        addrs = raw.get("shipping_addresses") or []
        addr = addrs[0] if addrs else {}
        return {
            "ext_id": str(raw.get("id") or ""),
            "name": f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip() or raw.get("email") or "",
            "email": raw.get("email") or "",
            "address": addr.get("address_1") or "",
            "city": addr.get("city") or "",
            "vat": "",
            "kvk": "",
            "phone": addr.get("phone") or raw.get("phone") or "",
            "zip": addr.get("postal_code") or "",
        }
    # Generic fallback
    return {
        "ext_id": str(raw.get("id") or ""),
        "name": raw.get("name") or raw.get("company") or raw.get("company_name") or raw.get("email") or "",
        "email": raw.get("email") or "",
        "address": raw.get("address") or raw.get("address1") or "",
        "city": raw.get("city") or "",
        "vat": raw.get("vat") or raw.get("tax_number") or "",
        "kvk": "",
        "phone": raw.get("phone") or "",
        "zip": raw.get("zipcode") or raw.get("zip") or raw.get("postcode") or "",
    }


def _normalize_invoice(provider: str, raw: dict, customer_names: dict) -> dict:
    """Normalize an invoice/order from any provider to a common shape.
    Field names verified against official API documentation per provider."""

    if provider == "perfex":
        # Themesic REST API: clientid, formatted_number, subtotal, total_tax, status (1-6)
        client_id = str(raw.get("clientid") or "")
        subtotal = _safe_float(raw.get("subtotal"))
        total_tax = _safe_float(raw.get("total_tax"))
        btw_rate = _guess_btw(subtotal, subtotal + total_tax)
        # Extract line items from Perfex items array
        lines = []
        for item in (raw.get("items") or []):
            lines.append({
                "desc": item.get("description") or "",
                "qty": _safe_float(item.get("qty") or 1),
                "price": _safe_float(item.get("rate")),
                "btwRate": _safe_float(item.get("taxrate")) if item.get("taxrate") else btw_rate,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("formatted_number") or raw.get("number") or "",
            "client": customer_names.get(client_id, f"Klant {client_id}"),
            "client_id": client_id,
            "date": raw.get("date"),
            "due_date": raw.get("duedate"),
            "subtotal": subtotal,
            "btw_rate": btw_rate,
            "status": {"1": "verzonden", "2": "betaald", "3": "verzonden", "4": "verlopen", "5": "concept", "6": "concept"}.get(str(raw.get("status")), "concept"),
            "notes": raw.get("clientnote") or raw.get("adminnote") or "",
            "lines": lines,
        }
    if provider == "moneybird":
        # Moneybird v2: invoice_id (display nr), state, total_price_excl_tax, invoice_date, due_date
        # States: draft, scheduled, open, pending_payment, reminded, late, paid, uncollectible
        contact = raw.get("contact") or {}
        contact_id = str(raw.get("contact_id") or "")
        btw_rate = _guess_btw(_safe_float(raw.get("total_price_excl_tax")), _safe_float(raw.get("total_price_incl_tax")))
        # Extract line items from Moneybird details array
        lines = []
        for detail in (raw.get("details") or []):
            lines.append({
                "desc": detail.get("description") or "",
                "qty": _safe_float(detail.get("amount_decimal") or detail.get("amount") or 1),
                "price": _safe_float(detail.get("price")),
                "btwRate": _safe_float(detail.get("tax_rate_id")) if detail.get("tax_rate_id") else btw_rate,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("invoice_id") or "",
            "client": contact.get("company_name") or f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip() or customer_names.get(contact_id, ""),
            "client_id": contact_id,
            "date": raw.get("invoice_date"),
            "due_date": raw.get("due_date"),
            "subtotal": _safe_float(raw.get("total_price_excl_tax")),
            "btw_rate": btw_rate,
            "status": {"open": "verzonden", "reminded": "verzonden", "pending_payment": "verzonden", "late": "verlopen", "paid": "betaald", "draft": "concept", "scheduled": "concept", "uncollectible": "verlopen"}.get(raw.get("state", ""), "concept"),
            "notes": raw.get("reference") or "",
            "lines": lines,
        }
    if provider == "wefact":
        # WeFact: InvoiceCode, Date, DueDate, AmountExcl, AmountIncl, Status, DebtorCode
        btw_rate = _guess_btw(_safe_float(raw.get("AmountExcl")), _safe_float(raw.get("AmountIncl")))
        # Extract line items from WeFact InvoiceLines array
        lines = []
        for line in (raw.get("InvoiceLines") or []):
            lines.append({
                "desc": line.get("Description") or "",
                "qty": _safe_float(line.get("Number") or 1),
                "price": _safe_float(line.get("PriceExcl")),
                "btwRate": _safe_float(line.get("TaxPercentage")) if line.get("TaxPercentage") else btw_rate,
            })
        return {
            "ext_id": str(raw.get("Identifier") or raw.get("InvoiceCode") or ""),
            "number": raw.get("InvoiceCode") or "",
            "client": customer_names.get(str(raw.get("DebtorCode")), raw.get("CompanyName") or ""),
            "client_id": str(raw.get("DebtorCode") or ""),
            "date": raw.get("Date"),
            "due_date": raw.get("DueDate"),
            "subtotal": _safe_float(raw.get("AmountExcl")),
            "btw_rate": btw_rate,
            "status": {"0": "concept", "1": "verzonden", "2": "betaald", "3": "verlopen"}.get(str(raw.get("Status")), "concept"),
            "notes": raw.get("Remark") or "",
            "lines": lines,
        }
    if provider == "snelstart":
        # SnelStart B2B: factuurnummer, factuurdatum, vervalDatum, factuurbedrag, openstaandSaldo
        # Extract line items from SnelStart boekingsregels array
        lines = []
        for regel in (raw.get("boekingsregels") or []):
            lines.append({
                "desc": regel.get("omschrijving") or "",
                "qty": 1,
                "price": _safe_float(regel.get("bedrag")),
                "btwRate": 21,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("factuurnummer") or "",
            "client": customer_names.get(str(raw.get("relatie", {}).get("id")), raw.get("relatie", {}).get("naam") or ""),
            "client_id": str(raw.get("relatie", {}).get("id") or ""),
            "date": (raw.get("factuurdatum") or "")[:10],
            "due_date": (raw.get("vervalDatum") or "")[:10],
            "subtotal": _safe_float(raw.get("factuurbedrag")),
            "btw_rate": 21,
            "status": "betaald" if _safe_float(raw.get("openstaandSaldo")) == 0 else "verzonden",
            "notes": raw.get("omschrijving") or "",
            "lines": lines,
        }
    if provider == "shopify":
        # Shopify Admin 2024-01: name (#1001), order_number (1001), total_price, subtotal_price,
        # total_tax, financial_status, billing_address, customer
        billing = raw.get("billing_address") or {}
        customer = raw.get("customer") or {}
        subtotal = _safe_float(raw.get("subtotal_price") or raw.get("total_price"))
        total_tax = _safe_float(raw.get("total_tax"))
        btw_rate = _guess_btw(subtotal, subtotal + total_tax) if subtotal > 0 else 21
        # Extract line items from Shopify line_items array
        lines = []
        for item in (raw.get("line_items") or []):
            item_tax_rate = btw_rate
            tax_lines = item.get("tax_lines") or []
            if tax_lines:
                item_tax_rate = round(_safe_float(tax_lines[0].get("rate")) * 100, 1)
            lines.append({
                "desc": item.get("name") or item.get("title") or "",
                "qty": _safe_float(item.get("quantity") or 1),
                "price": _safe_float(item.get("price")),
                "btwRate": item_tax_rate,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("name") or str(raw.get("order_number") or ""),
            "client": f"{billing.get('first_name', '') or customer.get('first_name', '')} {billing.get('last_name', '') or customer.get('last_name', '')}".strip() or raw.get("email") or "",
            "client_id": str(customer.get("id") or ""),
            "date": (raw.get("created_at") or "")[:10],
            "due_date": None,
            "subtotal": subtotal,
            "btw_rate": btw_rate,
            "status": {"paid": "betaald", "partially_paid": "verzonden", "pending": "concept", "refunded": "concept", "voided": "concept", "authorized": "verzonden"}.get(raw.get("financial_status", ""), "concept"),
            "notes": raw.get("note") or "",
            "lines": lines,
        }
    if provider == "woocommerce":
        # WooCommerce v3: number, status, total, total_tax, date_created, billing, customer_id
        # Statuses: pending, processing, on-hold, completed, cancelled, refunded, failed
        billing = raw.get("billing") or {}
        subtotal = _safe_float(raw.get("total"))
        total_tax = _safe_float(raw.get("total_tax"))
        btw_rate = _guess_btw(subtotal - total_tax, subtotal) if total_tax > 0 else 21
        # Extract line items from WooCommerce line_items array
        # WooCommerce: total = line total (excl tax), total_tax = tax for the line
        lines = []
        for item in (raw.get("line_items") or []):
            line_total = _safe_float(item.get("total"))
            line_tax = _safe_float(item.get("total_tax"))
            qty = _safe_float(item.get("quantity") or 1)
            unit_price = round(line_total / qty, 2) if qty else line_total
            item_btw = _guess_btw(line_total, line_total + line_tax) if line_total > 0 and line_tax > 0 else btw_rate
            lines.append({
                "desc": item.get("name") or "",
                "qty": qty,
                "price": unit_price,
                "btwRate": item_btw,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": raw.get("number") or str(raw.get("id") or ""),
            "client": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or raw.get("email") or billing.get("email") or "",
            "client_id": str(raw.get("customer_id") or ""),
            "date": (raw.get("date_created") or raw.get("date_created_gmt") or "")[:10],
            "due_date": None,
            "subtotal": subtotal,
            "btw_rate": btw_rate,
            "status": {"completed": "betaald", "processing": "verzonden", "on-hold": "verzonden", "pending": "concept", "cancelled": "concept", "refunded": "concept", "failed": "concept"}.get(raw.get("status", ""), "concept"),
            "notes": raw.get("customer_note") or "",
            "lines": lines,
        }
    if provider == "magento":
        # Magento REST V1: entity_id, increment_id, grand_total, subtotal, tax_amount,
        # state (1=open, 2=paid, 3=cancelled), created_at
        btw_rate = _guess_btw(_safe_float(raw.get("subtotal")), _safe_float(raw.get("grand_total"))) if _safe_float(raw.get("subtotal")) > 0 else 21
        # Extract line items from Magento items array
        lines = []
        for item in (raw.get("items") or []):
            lines.append({
                "desc": item.get("name") or item.get("sku") or "",
                "qty": _safe_float(item.get("qty") or item.get("qty_ordered") or 1),
                "price": _safe_float(item.get("price") or item.get("base_price")),
                "btwRate": btw_rate,
            })
        return {
            "ext_id": str(raw.get("entity_id") or raw.get("id") or ""),
            "number": raw.get("increment_id") or "",
            "client": f"{raw.get('customer_firstname', '')} {raw.get('customer_lastname', '')}".strip() or customer_names.get(str(raw.get("customer_id")), ""),
            "client_id": str(raw.get("customer_id") or ""),
            "date": (raw.get("created_at") or "")[:10],
            "due_date": None,
            "subtotal": _safe_float(raw.get("grand_total") or raw.get("subtotal")),
            "btw_rate": btw_rate,
            "status": {1: "verzonden", 2: "betaald", 3: "concept"}.get(raw.get("state"), "concept"),
            "notes": "",
            "lines": lines,
        }
    if provider == "medusa":
        # Medusa Admin: display_id, total (in CENTS!), subtotal, tax_total,
        # status, payment_status, customer_id
        # Money is in smallest unit (cents) — divide by 100
        total_cents = raw.get("total") or 0
        subtotal_cents = raw.get("subtotal") or total_cents
        tax_cents = raw.get("tax_total") or 0
        customer = raw.get("customer") or {}
        btw_rate = _guess_btw(subtotal_cents / 100, (subtotal_cents + tax_cents) / 100) if subtotal_cents > 0 else 21
        # Extract line items from Medusa items array (prices in cents!)
        lines = []
        for item in (raw.get("items") or []):
            item_tax = _safe_float(item.get("tax_total") or 0) / 100
            unit_price = _safe_float(item.get("unit_price") or 0) / 100
            item_btw = _guess_btw(unit_price, unit_price + (item_tax / _safe_float(item.get("quantity") or 1))) if unit_price > 0 and item_tax > 0 else btw_rate
            lines.append({
                "desc": item.get("title") or item.get("description") or "",
                "qty": _safe_float(item.get("quantity") or 1),
                "price": unit_price,
                "btwRate": item_btw,
            })
        return {
            "ext_id": str(raw.get("id") or ""),
            "number": str(raw.get("display_id") or ""),
            "client": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or raw.get("email") or customer_names.get(str(raw.get("customer_id")), ""),
            "client_id": str(raw.get("customer_id") or ""),
            "date": (raw.get("created_at") or "")[:10],
            "due_date": None,
            "subtotal": subtotal_cents / 100,
            "btw_rate": btw_rate,
            "status": {"captured": "betaald", "not_paid": "concept", "awaiting": "verzonden", "refunded": "concept"}.get(raw.get("payment_status", ""), {"completed": "betaald", "pending": "concept", "archived": "betaald"}.get(raw.get("status", ""), "concept")),
            "notes": "",
            "lines": lines,
        }
    # Generic fallback for unknown providers
    return {
        "ext_id": str(raw.get("id") or ""),
        "number": str(raw.get("number") or raw.get("invoice_number") or raw.get("invoice_id") or ""),
        "client": raw.get("name") or raw.get("customer_name") or raw.get("company_name") or "",
        "client_id": str(raw.get("customer_id") or raw.get("contact_id") or ""),
        "date": raw.get("date") or raw.get("created_at") or raw.get("invoice_date"),
        "due_date": raw.get("due_date"),
        "subtotal": _safe_float(raw.get("total") or raw.get("amount") or raw.get("grand_total")),
        "btw_rate": 21,
        "status": "concept",
        "notes": raw.get("notes") or raw.get("note") or raw.get("reference") or "",
        "lines": [],
    }


# ============================================================
# Universal import endpoint
# ============================================================

@router.post("/universal/{provider}")
async def universal_import(
    provider: str,
    company_id: str | None = None,
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
    # Resolve which company the UI is targeting. Falls back to the user's
    # own company if no ?company_id is passed. For accountants with multiple
    # client companies this is critical — otherwise every import lands in
    # the accountant's home company instead of the selected one.
    resolved = await _resolve_company_id(user, company_id, db)
    if not resolved:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")
    company_id = resolved

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
                kvk=norm.get("kvk") or None,
                address=norm["address"] or None,
                city=norm["city"] or None,
                phone=norm.get("phone") or None,
                zip=norm.get("zip") or None,
                state=norm.get("state") or None,
                country=norm.get("country") or None,
                website=norm.get("website") or None,
                extra=norm.get("extra") or None,
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

            # Use detailed line items when available, fall back to single-line total
            invoice_lines = norm.get("lines") or []
            if not invoice_lines:
                invoice_lines = [{
                    "desc": f"{norm['number'] or provider}",
                    "qty": 1,
                    "price": round(norm["subtotal"], 2),
                    "btwRate": btw_rate,
                }]
            else:
                # Round prices and normalize btw rates on provider line items
                for line in invoice_lines:
                    line["price"] = round(line["price"], 2)
                    lr = line.get("btwRate", btw_rate)
                    if abs(lr - 21) < 3:
                        line["btwRate"] = 21
                    elif abs(lr - 9) < 3:
                        line["btwRate"] = 9
                    elif abs(lr) < 2:
                        line["btwRate"] = 0

            db.add(Invoice(
                id=uuid.uuid4(),
                company_id=company_id,
                number=norm["number"] or f"{provider.upper()}-{norm['ext_id']}",
                client=norm["client"] or f"Klant {norm['client_id']}",
                client_id=norm["client_id"],
                date=_safe_date(norm["date"]),
                due_date=_safe_date(norm["due_date"]),
                lines=invoice_lines,
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
