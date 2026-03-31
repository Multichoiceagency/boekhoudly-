from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class VATCalculation(BaseModel):
    period: str
    start_date: date
    end_date: date
    btw_collected: Decimal
    btw_paid: Decimal
    btw_balance: Decimal
    breakdown: list[dict] | None = None


class VATReportResponse(BaseModel):
    id: UUID
    company_id: UUID
    period: str
    start_date: date
    end_date: date
    btw_collected: Decimal
    btw_paid: Decimal
    btw_balance: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
