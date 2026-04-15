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
from app.utils.auth import get_current_user

router = APIRouter(prefix="/workspace", tags=["Workspace"])


def _company_id(user: User) -> uuid.UUID:
    if not user.company_id:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")
    return user.company_id


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
async def list_invoices(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
    result = await db.execute(select(Invoice).where(Invoice.company_id == cid).order_by(Invoice.date.desc()))
    return [_inv_to_dict(i) for i in result.scalars().all()]


@router.post("/invoices", status_code=201)
async def create_invoice(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
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
    await db.execute(delete(Invoice).where(Invoice.id == invoice_id))
    return {"ok": True}


def _inv_to_dict(i: Invoice) -> dict:
    return {
        "id": str(i.id), "number": i.number, "client": i.client,
        "clientId": i.client_id or "", "date": str(i.date), "dueDate": str(i.due_date),
        "lines": i.lines or [], "status": i.status,
        "paidDate": str(i.paid_date) if i.paid_date else None,
    }


# ============================================================
#  EXPENSES
# ============================================================
@router.get("/expenses")
async def list_expenses(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
    result = await db.execute(select(Expense).where(Expense.company_id == cid).order_by(Expense.date.desc()))
    return [_exp_to_dict(e) for e in result.scalars().all()]


@router.post("/expenses", status_code=201)
async def create_expense(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
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
    await db.execute(delete(Expense).where(Expense.id == expense_id))
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
async def list_debtors(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
    result = await db.execute(select(Debtor).where(Debtor.company_id == cid).order_by(Debtor.name))
    return [_deb_to_dict(d) for d in result.scalars().all()]


@router.post("/debtors", status_code=201)
async def create_debtor(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
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
    mapping = {"paymentTerm": "payment_term"}
    for k, v in data.items():
        col = mapping.get(k, k)
        if hasattr(d, col):
            setattr(d, col, v)
    await db.flush()
    return _deb_to_dict(d)


@router.delete("/debtors/{debtor_id}")
async def delete_debtor(debtor_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Debtor).where(Debtor.id == debtor_id))
    return {"ok": True}


def _deb_to_dict(d: Debtor) -> dict:
    return {
        "id": str(d.id), "name": d.name, "email": d.email or "",
        "kvk": d.kvk or "", "btw": d.btw or "", "iban": d.iban or "",
        "paymentTerm": d.payment_term, "address": d.address or "", "city": d.city or "",
    }


# ============================================================
#  CREDITORS
# ============================================================
@router.get("/creditors")
async def list_creditors(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
    result = await db.execute(select(Creditor).where(Creditor.company_id == cid).order_by(Creditor.name))
    return [_cred_to_dict(c) for c in result.scalars().all()]


@router.post("/creditors", status_code=201)
async def create_creditor(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
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
    await db.execute(delete(Creditor).where(Creditor.id == creditor_id))
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
async def list_bank_transactions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
    result = await db.execute(select(BankTransaction).where(BankTransaction.company_id == cid).order_by(BankTransaction.date.desc()))
    return [_bt_to_dict(t) for t in result.scalars().all()]


@router.post("/bank-transactions", status_code=201)
async def create_bank_transaction(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = _company_id(user)
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
