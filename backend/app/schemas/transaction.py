from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class TransactionCreate(BaseModel):
    amount: Decimal
    date: date
    description: str
    type: str
    category: str | None = None
    btw_percentage: Decimal | None = None
    source: str = "manual"


class TransactionResponse(BaseModel):
    id: UUID
    company_id: UUID
    amount: Decimal
    date: date
    description: str
    type: str
    category: str | None = None
    btw_percentage: Decimal | None = None
    btw_amount: Decimal | None = None
    source: str
    status: str
    confidence_score: float | None = None
    ai_category: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionList(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int = 1
    per_page: int = 20


class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    pending_count: int
    processed_count: int
