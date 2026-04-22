"""
Workspace CRUD API — all data persisted to PostgreSQL.
Handles invoices, expenses, debtors, creditors, bank transactions, and companies.
"""
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.expense import Expense
from app.models.debtor import Debtor
from app.models.creditor import Creditor
from app.models.bank_transaction import BankTransaction
from app.models.product import Product
from app.utils.auth import get_current_user

router = APIRouter(prefix="/workspace", tags=["Workspace"])


def _company_id(user: User) -> uuid.UUID | None:
    """Return the user's company_id, or None for admins (meaning 'all companies')."""
    if user.role == "admin":
        return user.company_id  # may be None — caller handles it
    if not user.company_id:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")
    return user.company_id


async def _assert_company_access(
    user: User,
    entity_company_id: uuid.UUID | None,
    db: AsyncSession,
) -> None:
    """Raise 403 if the user cannot touch a record belonging to
    `entity_company_id`. Admins pass through; accountants must own it via
    CompanySubscription; regular users must match exactly.

    Needed because mutation endpoints look up entities by their own UUID
    (e.g. /invoices/{id}) and previously did no tenant check — any
    authenticated user could mutate any record if they learned the UUID.
    """
    if entity_company_id is None:
        # Legacy rows without a company — allow admin only.
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")
        return
    if user.role == "admin":
        return
    if user.role == "accountant":
        from app.models.company_subscription import CompanySubscription
        result = await db.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id == entity_company_id,
                CompanySubscription.accountant_id == user.id,
            )
        )
        if result.scalar_one_or_none() or user.company_id == entity_company_id:
            return
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")
    if user.company_id == entity_company_id:
        return
    raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")


async def _resolve_company_id(
    user: User,
    requested_id: str | None,
    db: AsyncSession,
) -> uuid.UUID | None:
    """Resolve the target company ID, validating access.

    When the caller passes ?company_id=... (the company the UI is currently
    viewing), this returns that company's UUID if the user is allowed to see
    it. Without an override, falls back to the user's own home company.
    """
    if not requested_id:
        return _company_id(user)
    try:
        cid = uuid.UUID(str(requested_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Ongeldig company_id")

    if user.role == "admin":
        return cid
    if user.role == "accountant":
        from app.models.company_subscription import CompanySubscription
        result = await db.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id == cid,
                CompanySubscription.accountant_id == user.id,
            )
        )
        if result.scalar_one_or_none() or user.company_id == cid:
            return cid
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")
    if user.company_id == cid:
        return cid
    raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")


# ============================================================
#  COMPANIES
# ============================================================
@router.get("/companies")
async def list_companies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return companies the user is allowed to see.

    - admin: all companies
    - accountant: companies they own via CompanySubscription.accountant_id
                  + their own home company
    - user: only their own company
    """
    from app.models.company_subscription import CompanySubscription

    if user.role == "admin":
        result = await db.execute(select(Company).order_by(Company.created_at.desc()))
        companies = result.scalars().all()
    elif user.role == "accountant":
        sub_result = await db.execute(
            select(CompanySubscription.company_id).where(CompanySubscription.accountant_id == user.id)
        )
        ids = [r[0] for r in sub_result.all()]
        if user.company_id and user.company_id not in ids:
            ids.append(user.company_id)
        if not ids:
            return []
        result = await db.execute(select(Company).where(Company.id.in_(ids)).order_by(Company.created_at.desc()))
        companies = result.scalars().all()
    else:
        if not user.company_id:
            return []
        result = await db.execute(select(Company).where(Company.id == user.company_id))
        companies = result.scalars().all()

    return [_company_to_dict(c) for c in companies]


@router.post("/companies", status_code=201)
async def create_company(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a company. If the user is an accountant, automatically create
    a CompanySubscription linking the accountant to the new company so it
    appears on their billing summary."""
    from app.models.subscription_plan import SubscriptionPlan
    from app.models.company_subscription import CompanySubscription
    from datetime import date

    c = Company(
        id=uuid.uuid4(),
        name=data.get("name", ""),
        kvk_number=data.get("kvk", ""),
        btw_number=data.get("btw", ""),
        address=data.get("address"),
        city=data.get("city"),
        postal_code=data.get("postcode"),
        iban=data.get("iban"),
        phone=data.get("phone"),
        industry=data.get("activiteiten"),
        company_type=data.get("type"),
        primary_color=data.get("primaryColor", "#059669"),
    )
    db.add(c)
    await db.flush()

    if not user.company_id:
        user.company_id = c.id
        await db.flush()

    # Auto-create subscription for accountants and admins
    if user.role in ("accountant", "admin"):
        plan_slug = data.get("plan_slug", "starter")
        plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug))
        plan = plan_result.scalar_one_or_none()
        if not plan:
            # Fallback to any active plan
            any_plan_result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.sort_order)
            )
            plan = any_plan_result.scalars().first()

        if plan:
            sub = CompanySubscription(
                id=uuid.uuid4(),
                company_id=c.id,
                plan_id=plan.id,
                accountant_id=user.id if user.role == "accountant" else None,
                period_start=date.today(),
                ai_credits_used=0,
                ai_cost_eur_cents=0,
                status="active",
            )
            db.add(sub)
            await db.flush()

    return _company_to_dict(c)


@router.put("/companies/{company_id}")
async def update_company(company_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Bedrijf niet gevonden")
    for field in ["name", "kvk_number", "btw_number", "address", "city", "postal_code", "iban", "phone", "industry", "company_type", "primary_color", "logo_url"]:
        if field in data:
            setattr(c, field, data[field])
    # Handle branding fields mapped to company columns
    if "companyName" in data:
        c.name = data["companyName"]
    if "kvk" in data:
        c.kvk_number = data["kvk"]
    if "btw" in data:
        c.btw_number = data["btw"]
    if "postcode" in data:
        c.postal_code = data["postcode"]
    if "primaryColor" in data:
        c.primary_color = data["primaryColor"]
    if "logo" in data:
        c.logo_url = data["logo"]  # Can be base64 data URL or external URL
    if "website" in data:
        # Store in settings JSONB
        settings = c.settings or {}
        settings["website"] = data["website"]
        c.settings = settings
    if "email" in data:
        settings = c.settings or {}
        settings["email"] = data["email"]
        c.settings = settings
    await db.flush()
    return _company_to_dict(c)


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Delete a company and all its related data.

    Only admins and accountants (who own the company) can delete.
    Cascades to invoices, expenses, debtors, creditors, bank transactions,
    products, documents, subscriptions, and unlinks users.
    """
    from app.models.document import Document
    from app.models.company_subscription import CompanySubscription
    from app.models.integration_connection import IntegrationConnection
    from app.models.cloud_connection import CloudConnection
    from app.models.bank_connection import BankConnection
    from app.models.crm_cache import CrmRecord, CrmSyncRun
    from app.models.ai_usage import AiUsage
    from app.models.vat_report import VATReport
    from app.models.transaction import Transaction
    from app.models.ledger_entry import LedgerEntry

    result = await db.execute(select(Company).where(Company.id == company_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Bedrijf niet gevonden")

    # Authorisation
    if user.role == "admin":
        pass
    elif user.role == "accountant":
        sub_check = await db.execute(
            select(CompanySubscription).where(
                CompanySubscription.company_id == c.id,
                CompanySubscription.accountant_id == user.id,
            )
        )
        if not sub_check.scalar_one_or_none() and user.company_id != c.id:
            raise HTTPException(status_code=403, detail="Geen rechten om dit bedrijf te verwijderen")
    else:
        raise HTTPException(status_code=403, detail="Geen rechten om bedrijven te verwijderen")

    # Cascade deletes (no FK ON DELETE CASCADE is defined — do it explicitly).
    # Order matters: child rows first, then the company row itself.
    await db.execute(delete(LedgerEntry).where(LedgerEntry.company_id == c.id))
    await db.execute(delete(Transaction).where(Transaction.company_id == c.id))
    await db.execute(delete(VATReport).where(VATReport.company_id == c.id))
    await db.execute(delete(AiUsage).where(AiUsage.company_id == c.id))
    await db.execute(delete(CrmRecord).where(CrmRecord.company_id == c.id))
    await db.execute(delete(CrmSyncRun).where(CrmSyncRun.company_id == c.id))
    await db.execute(delete(IntegrationConnection).where(IntegrationConnection.company_id == c.id))
    await db.execute(delete(CloudConnection).where(CloudConnection.company_id == c.id))
    await db.execute(delete(BankConnection).where(BankConnection.company_id == c.id))
    await db.execute(delete(Invoice).where(Invoice.company_id == c.id))
    await db.execute(delete(Expense).where(Expense.company_id == c.id))
    await db.execute(delete(Debtor).where(Debtor.company_id == c.id))
    await db.execute(delete(Creditor).where(Creditor.company_id == c.id))
    await db.execute(delete(BankTransaction).where(BankTransaction.company_id == c.id))
    await db.execute(delete(Product).where(Product.company_id == c.id))
    await db.execute(delete(Document).where(Document.company_id == c.id))
    await db.execute(delete(CompanySubscription).where(CompanySubscription.company_id == c.id))

    # Unlink users pointing at this company (don't delete users)
    from sqlalchemy import update
    await db.execute(update(User).where(User.company_id == c.id).values(company_id=None))

    await db.delete(c)
    await db.flush()
    return {"ok": True, "id": str(c.id)}


def _company_to_dict(c: Company) -> dict:
    settings = c.settings or {}
    return {
        "id": str(c.id), "name": c.name or "", "type": c.company_type or "",
        "kvk": c.kvk_number or "", "btw": c.btw_number or "",
        "activiteiten": c.industry or "", "parentId": None, "agents": [],
        "branding": {
            "logo": c.logo_url, "primaryColor": c.primary_color or "#059669",
            "companyName": c.name or "", "address": c.address or "",
            "postcode": c.postal_code or "", "city": c.city or "",
            "kvk": c.kvk_number or "", "btw": c.btw_number or "",
            "iban": c.iban or "", "email": settings.get("email", ""),
            "phone": c.phone or "", "website": settings.get("website", ""),
        },
    }


# ============================================================
#  INVOICES
# ============================================================
@router.get("/invoices")
async def list_invoices(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Invoice).order_by(Invoice.date.desc())
    if cid:
        q = q.where(Invoice.company_id == cid)
    result = await db.execute(q)
    return [_inv_to_dict(i) for i in result.scalars().all()]


@router.post("/invoices", status_code=201)
async def create_invoice(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    inv = Invoice(
        id=uuid.uuid4(), company_id=cid,
        number=data.get("number", ""), client=data.get("client", ""),
        client_id=data.get("clientId"), date=_parse_date(data.get("date")),
        due_date=_parse_date(data.get("dueDate")), lines=data.get("lines", []),
        status=data.get("status", "concept"), paid_date=_parse_date(data.get("paidDate")),
    )
    db.add(inv)
    await db.flush()
    return _inv_to_dict(inv)


@router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factuur niet gevonden")
    await _assert_company_access(user, inv.company_id, db)
    for k, v in data.items():
        col = {"clientId": "client_id", "dueDate": "due_date", "paidDate": "paid_date"}.get(k, k)
        if col in ("date", "due_date", "paid_date"):
            v = _parse_date(v)
        if hasattr(inv, col):
            setattr(inv, col, v)
    await db.flush()
    return _inv_to_dict(inv)


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        return {"ok": True}
    await _assert_company_access(user, inv.company_id, db)
    await db.delete(inv)
    await db.flush()
    return {"ok": True}


def _inv_to_dict(i: Invoice) -> dict:
    return {
        "id": str(i.id), "number": i.number, "client": i.client,
        "clientId": i.client_id or "", "date": str(i.date), "dueDate": str(i.due_date),
        "lines": i.lines or [], "status": i.status,
        "paidDate": str(i.paid_date) if i.paid_date else None,
        "notes": i.notes or "",
        "source": getattr(i, 'source', 'manual') or 'manual',
        "sourceId": getattr(i, 'source_id', None),
        "documentType": getattr(i, 'document_type', 'factuur') or 'factuur',
        "relatedInvoiceId": getattr(i, 'related_invoice_id', None),
    }


# ============================================================
#  EXPENSES
# ============================================================
@router.get("/expenses")
async def list_expenses(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Expense).order_by(Expense.date.desc())
    if cid:
        q = q.where(Expense.company_id == cid)
    result = await db.execute(q)
    return [_exp_to_dict(e) for e in result.scalars().all()]


@router.post("/expenses", status_code=201)
async def create_expense(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    exp = Expense(
        id=uuid.uuid4(), company_id=cid,
        date=_parse_date(data.get("date")), description=data.get("description", ""),
        category=data.get("category", "Overig"), amount=float(data.get("amount", 0)),
        btw_rate=float(data.get("btwRate", 21)), status=data.get("status", "concept"),
        supplier_id=data.get("supplierId"),
    )
    db.add(exp)
    await db.flush()
    return _exp_to_dict(exp)


@router.put("/expenses/{expense_id}")
async def update_expense(expense_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Uitgave niet gevonden")
    await _assert_company_access(user, exp.company_id, db)
    mapping = {"btwRate": "btw_rate", "supplierId": "supplier_id"}
    for k, v in data.items():
        col = mapping.get(k, k)
        if col == "date":
            v = _parse_date(v)
        if col == "amount":
            v = float(v)
        if hasattr(exp, col):
            setattr(exp, col, v)
    await db.flush()
    return _exp_to_dict(exp)


@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    exp = result.scalar_one_or_none()
    if not exp:
        return {"ok": True}
    await _assert_company_access(user, exp.company_id, db)
    await db.delete(exp)
    await db.flush()
    return {"ok": True}


def _exp_to_dict(e: Expense) -> dict:
    return {
        "id": str(e.id), "date": str(e.date), "description": e.description,
        "category": e.category, "amount": float(e.amount), "btwRate": float(e.btw_rate),
        "status": e.status, "supplierId": e.supplier_id,
    }


# ============================================================
#  DEBTORS
# ============================================================
@router.get("/debtors")
async def list_debtors(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Debtor).order_by(Debtor.name)
    if cid:
        q = q.where(Debtor.company_id == cid)
    result = await db.execute(q)
    return [_deb_to_dict(d) for d in result.scalars().all()]


@router.post("/debtors", status_code=201)
async def create_debtor(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    d = Debtor(
        id=uuid.uuid4(), company_id=cid,
        name=data.get("name", ""), email=data.get("email"),
        kvk=data.get("kvk"), btw=data.get("btw"),
        iban=data.get("iban"), payment_term=int(data.get("paymentTerm", 30)),
        address=data.get("address"), city=data.get("city"),
    )
    db.add(d)
    await db.flush()
    return _deb_to_dict(d)


@router.put("/debtors/{debtor_id}")
async def update_debtor(debtor_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Debiteur niet gevonden")
    await _assert_company_access(user, d.company_id, db)
    mapping = {"paymentTerm": "payment_term"}
    for k, v in data.items():
        col = mapping.get(k, k)
        if hasattr(d, col):
            setattr(d, col, v)
    await db.flush()
    return _deb_to_dict(d)


@router.delete("/debtors/{debtor_id}")
async def delete_debtor(debtor_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Debtor).where(Debtor.id == debtor_id))
    d = result.scalar_one_or_none()
    if not d:
        return {"ok": True}
    await _assert_company_access(user, d.company_id, db)
    await db.delete(d)
    await db.flush()
    return {"ok": True}


def _deb_to_dict(d: Debtor) -> dict:
    return {
        "id": str(d.id), "name": d.name, "email": d.email or "",
        "kvk": d.kvk or "", "btw": d.btw or "", "iban": d.iban or "",
        "paymentTerm": d.payment_term, "address": d.address or "", "city": d.city or "",
        "source": getattr(d, 'source', 'manual') or 'manual',
        "sourceId": getattr(d, 'source_id', None),
    }


# ============================================================
#  CREDITORS
# ============================================================
@router.get("/creditors")
async def list_creditors(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Creditor).order_by(Creditor.name)
    if cid:
        q = q.where(Creditor.company_id == cid)
    result = await db.execute(q)
    return [_cred_to_dict(c) for c in result.scalars().all()]


@router.post("/creditors", status_code=201)
async def create_creditor(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    c = Creditor(
        id=uuid.uuid4(), company_id=cid,
        name=data.get("name", ""), email=data.get("email"),
        category=data.get("category", "Overig"), iban=data.get("iban"),
        payment_term=int(data.get("paymentTerm", 30)),
    )
    db.add(c)
    await db.flush()
    return _cred_to_dict(c)


@router.delete("/creditors/{creditor_id}")
async def delete_creditor(creditor_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Creditor).where(Creditor.id == creditor_id))
    c = result.scalar_one_or_none()
    if not c:
        return {"ok": True}
    await _assert_company_access(user, c.company_id, db)
    await db.delete(c)
    await db.flush()
    return {"ok": True}


def _cred_to_dict(c: Creditor) -> dict:
    return {
        "id": str(c.id), "name": c.name, "email": c.email or "",
        "category": c.category, "iban": c.iban or "", "paymentTerm": c.payment_term,
    }


# ============================================================
#  BANK TRANSACTIONS
# ============================================================
@router.get("/bank-transactions")
async def list_bank_transactions(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(BankTransaction).order_by(BankTransaction.date.desc())
    if cid:
        q = q.where(BankTransaction.company_id == cid)
    result = await db.execute(q)
    return [_bt_to_dict(t) for t in result.scalars().all()]


@router.post("/bank-transactions", status_code=201)
async def create_bank_transaction(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    t = BankTransaction(
        id=uuid.uuid4(), company_id=cid,
        date=_parse_date(data.get("date")), description=data.get("description", ""),
        amount=float(data.get("amount", 0)), category=data.get("category", ""),
        matched=data.get("matched", False),
        matched_invoice_id=data.get("matchedInvoiceId"),
        matched_expense_id=data.get("matchedExpenseId"),
    )
    db.add(t)
    await db.flush()
    return _bt_to_dict(t)


@router.put("/bank-transactions/{tx_id}")
async def update_bank_transaction(tx_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BankTransaction).where(BankTransaction.id == tx_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")
    await _assert_company_access(user, t.company_id, db)
    mapping = {"matchedInvoiceId": "matched_invoice_id", "matchedExpenseId": "matched_expense_id"}
    for k, v in data.items():
        col = mapping.get(k, k)
        if hasattr(t, col):
            setattr(t, col, v)
    await db.flush()
    return _bt_to_dict(t)


def _bt_to_dict(t: BankTransaction) -> dict:
    return {
        "id": str(t.id), "date": str(t.date), "description": t.description,
        "amount": float(t.amount), "category": t.category,
        "matched": t.matched, "matchedInvoiceId": t.matched_invoice_id,
        "matchedExpenseId": t.matched_expense_id,
    }


# ============================================================
#  HELPERS
# ============================================================
def _parse_date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val)[:10])
    except (ValueError, TypeError):
        return None


# ============================================================
#  OFFERTES (quotes) — document_type='offerte'
# ============================================================
@router.get("/offertes")
async def list_offertes(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Invoice).where(Invoice.document_type == "offerte").order_by(Invoice.date.desc())
    if cid:
        q = q.where(Invoice.company_id == cid)
    return [_inv_to_dict(i) for i in (await db.execute(q)).scalars().all()]


@router.post("/offertes", status_code=201)
async def create_offerte(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    if not cid:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld")
    inv = Invoice(
        id=uuid.uuid4(), company_id=cid, document_type="offerte",
        number=data.get("number", ""), client=data.get("client", ""),
        client_id=data.get("clientId"), date=_parse_date(data.get("date")) or date.today(),
        due_date=_parse_date(data.get("dueDate")) or date.today(),
        lines=data.get("lines", []), status=data.get("status", "concept"),
        notes=data.get("notes"),
    )
    db.add(inv)
    await db.flush()
    return _inv_to_dict(inv)


@router.post("/offertes/{offerte_id}/convert-to-invoice")
async def convert_offerte_to_invoice(offerte_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Convert an offerte to a factuur. Creates a new invoice with the same lines."""
    result = await db.execute(select(Invoice).where(Invoice.id == offerte_id))
    offerte = result.scalar_one_or_none()
    if not offerte or offerte.document_type != "offerte":
        raise HTTPException(status_code=404, detail="Offerte niet gevonden")
    await _assert_company_access(user, offerte.company_id, db)

    # Mark offerte as converted
    offerte.status = "omgezet"

    # Create the invoice
    inv = Invoice(
        id=uuid.uuid4(), company_id=offerte.company_id, document_type="factuur",
        number="",
        client=offerte.client, client_id=offerte.client_id,
        date=date.today(), due_date=date.today(),
        lines=offerte.lines, status="concept",
        notes=f"Omgezet vanuit offerte {offerte.number}",
        related_invoice_id=str(offerte.id),
    )
    db.add(inv)
    await db.flush()
    return _inv_to_dict(inv)


# ============================================================
#  CREDITNOTA'S — document_type='creditnota'
# ============================================================
@router.get("/creditnotas")
async def list_creditnotas(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Invoice).where(Invoice.document_type == "creditnota").order_by(Invoice.date.desc())
    if cid:
        q = q.where(Invoice.company_id == cid)
    return [_inv_to_dict(i) for i in (await db.execute(q)).scalars().all()]


@router.post("/creditnotas", status_code=201)
async def create_creditnota(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    if not cid:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld")
    cn = Invoice(
        id=uuid.uuid4(), company_id=cid, document_type="creditnota",
        number=data.get("number", ""), client=data.get("client", ""),
        client_id=data.get("clientId"), date=_parse_date(data.get("date")) or date.today(),
        due_date=_parse_date(data.get("dueDate")) or date.today(),
        lines=data.get("lines", []), status=data.get("status", "concept"),
        notes=data.get("notes"),
        related_invoice_id=data.get("relatedInvoiceId"),
    )
    db.add(cn)
    await db.flush()
    return _inv_to_dict(cn)


@router.post("/creditnotas/from-invoice/{invoice_id}")
async def create_creditnota_from_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a credit note that reverses a specific invoice."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    orig = result.scalar_one_or_none()
    if not orig:
        raise HTTPException(status_code=404, detail="Factuur niet gevonden")
    await _assert_company_access(user, orig.company_id, db)

    # Negate amounts
    neg_lines = [
        {**l, "price": -abs(l.get("price", 0))}
        for l in (orig.lines or [])
    ]
    cn = Invoice(
        id=uuid.uuid4(), company_id=orig.company_id, document_type="creditnota",
        number="", client=orig.client, client_id=orig.client_id,
        date=date.today(), due_date=date.today(),
        lines=neg_lines, status="concept",
        notes=f"Creditnota voor factuur {orig.number}",
        related_invoice_id=str(orig.id),
    )
    db.add(cn)
    await db.flush()
    return _inv_to_dict(cn)


# ============================================================
#  PRODUCTEN (catalog)
# ============================================================
@router.get("/producten")
async def list_producten(company_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, company_id, db)
    q = select(Product).order_by(Product.sort_order, Product.name)
    if cid:
        q = q.where(Product.company_id == cid)
    return [_prod_to_dict(p) for p in (await db.execute(q)).scalars().all()]


@router.post("/producten", status_code=201)
async def create_product(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _resolve_company_id(user, data.get("companyId"), db)
    if not cid:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld")
    p = Product(
        id=uuid.uuid4(), company_id=cid,
        name=data.get("name", ""), description=data.get("description"),
        price=float(data.get("price", 0)), btw_rate=float(data.get("btwRate", 21)),
        unit=data.get("unit", "stuk"), sku=data.get("sku"),
        category=data.get("category"), is_active=data.get("isActive", True),
    )
    db.add(p)
    await db.flush()
    return _prod_to_dict(p)


@router.put("/producten/{product_id}")
async def update_product(product_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product niet gevonden")
    await _assert_company_access(user, p.company_id, db)
    mapping = {"btwRate": "btw_rate", "isActive": "is_active", "sortOrder": "sort_order"}
    for k, v in data.items():
        col = mapping.get(k, k)
        if col == "price":
            v = float(v)
        if hasattr(p, col):
            setattr(p, col, v)
    await db.flush()
    return _prod_to_dict(p)


@router.delete("/producten/{product_id}")
async def delete_product(product_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    p = result.scalar_one_or_none()
    if not p:
        return {"ok": True}
    await _assert_company_access(user, p.company_id, db)
    await db.delete(p)
    await db.flush()
    return {"ok": True}


def _prod_to_dict(p: Product) -> dict:
    return {
        "id": str(p.id), "name": p.name, "description": p.description or "",
        "price": float(p.price), "btwRate": float(p.btw_rate),
        "unit": p.unit, "sku": p.sku or "", "category": p.category or "",
        "isActive": p.is_active, "sortOrder": p.sort_order,
    }
