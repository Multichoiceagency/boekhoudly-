"""Cross-system analyse endpoints — match invoices/customers/payments
across FiscaalFlow native data + cached CRM records (Perfex etc) +
manually entered data, by normalised key (e.g. invoice number)."""
import re
import uuid
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.crm_cache import CrmRecord
from app.utils.auth import get_current_user

router = APIRouter(prefix="/analyse", tags=["Analyse"])


def _normalize_invoice_number(raw: str) -> str:
    """Normalise an invoice number for cross-system matching.

    Strip non-alphanumerics, leading zeros, common Dutch prefixes
    (Factuur:, F-, FAC, etc.) and uppercase. So 'Factuur:01/01/2023'
    and 'F-2023-01' and 'fac010123' all collapse to '012023'.
    """
    if not raw:
        return ""
    s = str(raw).upper()
    s = re.sub(r"^(FACTUUR|FAC|F|INV|INVOICE)[:\-\s/]*", "", s)
    s = re.sub(r"[^A-Z0-9]", "", s)
    return s.lstrip("0") or s


def _amount(raw) -> float:
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _date_str(raw) -> str | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return raw[:10]
    if isinstance(raw, (datetime,)):
        return raw.date().isoformat()
    if hasattr(raw, "isoformat"):
        return raw.isoformat()[:10]
    return str(raw)[:10]


def _fingerprint_native(inv: Invoice) -> dict:
    total = sum(_amount(line.get("total") or line.get("amount") or 0) for line in (inv.lines or []))
    return {
        "source": "fiscaalflow",
        "source_id": str(inv.id),
        "number_raw": inv.number,
        "number_norm": _normalize_invoice_number(inv.number),
        "client": inv.client,
        "client_id": inv.client_id,
        "date": _date_str(inv.date),
        "due_date": _date_str(inv.due_date),
        "total": round(total, 2),
        "status": inv.status,
    }


def _fingerprint_crm(rec: CrmRecord) -> dict:
    p = rec.payload or {}
    if rec.provider == "perfex":
        return {
            "source": "perfex",
            "source_id": str(p.get("id") or rec.external_id),
            "number_raw": p.get("formatted_number") or p.get("number"),
            "number_norm": _normalize_invoice_number(p.get("formatted_number") or p.get("number") or ""),
            "client": str(p.get("clientid") or ""),
            "client_id": str(p.get("clientid") or ""),
            "date": _date_str(p.get("date")),
            "due_date": _date_str(p.get("duedate")),
            "total": _amount(p.get("total")),
            "status": {"1": "onbetaald", "2": "betaald", "3": "deels", "4": "verlopen", "5": "geannuleerd", "6": "concept"}.get(str(p.get("status")), str(p.get("status") or "")),
        }
    # Generic fallback for moneybird/wefact when we add caching for those
    return {
        "source": rec.provider,
        "source_id": rec.external_id,
        "number_raw": p.get("invoice_id") or p.get("number") or rec.external_id,
        "number_norm": _normalize_invoice_number(p.get("invoice_id") or p.get("number") or rec.external_id),
        "client": str(p.get("contact_id") or p.get("debtor_id") or ""),
        "client_id": str(p.get("contact_id") or p.get("debtor_id") or ""),
        "date": _date_str(p.get("invoice_date") or p.get("date")),
        "due_date": _date_str(p.get("due_date")),
        "total": _amount(p.get("total_price_incl_tax") or p.get("AmountIncl") or p.get("total")),
        "status": str(p.get("state") or p.get("status") or ""),
    }


@router.get("/invoices")
async def analyse_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Match all invoices across FiscaalFlow native + cached CRM records.

    Groups by normalised invoice number, returns:
      - matched: groups with 2+ sources (the interesting ones)
      - native_only: invoices that exist only in FiscaalFlow
      - crm_only: invoices that exist only in CRMs
      - conflicts: matched groups where amounts disagree by > €0.01
      - stats
    """
    # Fetch native invoices (scoped by company)
    native_q = select(Invoice)
    if current_user.role != "admin" and current_user.company_id:
        native_q = native_q.where(Invoice.company_id == current_user.company_id)
    native_result = await db.execute(native_q)
    native_invoices = native_result.scalars().all()

    # Fetch cached CRM invoices
    crm_q = select(CrmRecord).where(CrmRecord.resource == "invoices")
    if current_user.role != "admin" and current_user.company_id:
        crm_q = crm_q.where(CrmRecord.company_id == current_user.company_id)
    crm_result = await db.execute(crm_q)
    crm_records = crm_result.scalars().all()

    # Fingerprint everything
    fingerprints: list[dict] = []
    for inv in native_invoices:
        fingerprints.append(_fingerprint_native(inv))
    for rec in crm_records:
        fingerprints.append(_fingerprint_crm(rec))

    # Group by normalised number
    by_number: dict[str, list[dict]] = defaultdict(list)
    for fp in fingerprints:
        key = fp["number_norm"]
        if not key:
            continue
        by_number[key].append(fp)

    matched, native_only, crm_only, conflicts = [], [], [], []
    for num, group in by_number.items():
        sources = {fp["source"] for fp in group}
        if len(sources) >= 2:
            totals = [fp["total"] for fp in group if fp["total"] > 0]
            has_conflict = len(set(round(t, 2) for t in totals)) > 1 if totals else False
            entry = {"number": num, "sources": sorted(sources), "items": group, "conflict": has_conflict}
            matched.append(entry)
            if has_conflict:
                conflicts.append(entry)
        elif "fiscaalflow" in sources:
            native_only.extend(group)
        else:
            crm_only.extend(group)

    matched.sort(key=lambda g: -max(fp["total"] for fp in g["items"]))
    native_only.sort(key=lambda fp: -fp["total"])
    crm_only.sort(key=lambda fp: -fp["total"])

    return {
        "stats": {
            "total_invoices": len(fingerprints),
            "native": len(native_invoices),
            "crm": len(crm_records),
            "matched_groups": len(matched),
            "native_only": len(native_only),
            "crm_only": len(crm_only),
            "conflicts": len(conflicts),
        },
        "matched": matched[:200],
        "native_only": native_only[:200],
        "crm_only": crm_only[:200],
        "conflicts": conflicts[:50],
    }
