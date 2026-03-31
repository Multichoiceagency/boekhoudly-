import uuid
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionList,
    TransactionSummary,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transacties"])


@router.get("/", response_model=TransactionList)
async def list_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal transacties op met filters."""
    query = select(Transaction).where(Transaction.company_id == current_user.company_id)

    if type:
        query = query.where(Transaction.type == type)
    if category:
        query = query.where(Transaction.category == category)
    if status:
        query = query.where(Transaction.status == status)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Transaction.date.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return TransactionList(items=items, total=total, page=page, per_page=per_page)


@router.get("/summary", response_model=TransactionSummary)
async def get_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal samenvatting van transacties op."""
    base = select(Transaction).where(Transaction.company_id == current_user.company_id)
    if date_from:
        base = base.where(Transaction.date >= date_from)
    if date_to:
        base = base.where(Transaction.date <= date_to)

    income_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.company_id == current_user.company_id,
        Transaction.type == TransactionType.INCOME,
    )
    expense_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.company_id == current_user.company_id,
        Transaction.type == TransactionType.EXPENSE,
    )
    pending_q = select(func.count()).where(
        Transaction.company_id == current_user.company_id,
        Transaction.status == TransactionStatus.PENDING,
    )
    processed_q = select(func.count()).where(
        Transaction.company_id == current_user.company_id,
        Transaction.status == TransactionStatus.PROCESSED,
    )

    income = (await db.execute(income_q)).scalar() or Decimal("0")
    expenses = (await db.execute(expense_q)).scalar() or Decimal("0")
    pending = (await db.execute(pending_q)).scalar() or 0
    processed = (await db.execute(processed_q)).scalar() or 0

    return TransactionSummary(
        total_income=income,
        total_expenses=expenses,
        net_profit=income - expenses,
        pending_count=pending,
        processed_count=processed,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal een enkele transactie op."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.company_id == current_user.company_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Werk een transactie bij."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.company_id == current_user.company_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")

    txn.amount = data.amount
    txn.date = data.date
    txn.description = data.description
    txn.type = data.type
    txn.category = data.category
    txn.btw_percentage = data.btw_percentage
    txn.status = TransactionStatus.REVIEWED
    await db.flush()
    return txn


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verwijder een transactie."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.company_id == current_user.company_id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transactie niet gevonden")

    await db.delete(txn)
