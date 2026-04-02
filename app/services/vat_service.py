import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.vat_report import VATReport, VATStatus


def parse_period(period: str) -> tuple[date, date]:
    """Parse een periode string (bijv. '2026-Q1') naar start en einddatum."""
    parts = period.split("-")
    year = int(parts[0])
    quarter = parts[1].upper()

    quarter_dates = {
        "Q1": (date(year, 1, 1), date(year, 3, 31)),
        "Q2": (date(year, 4, 1), date(year, 6, 30)),
        "Q3": (date(year, 7, 1), date(year, 9, 30)),
        "Q4": (date(year, 10, 1), date(year, 12, 31)),
    }

    if quarter not in quarter_dates:
        raise ValueError(f"Ongeldige periode: {period}. Gebruik formaat: 2026-Q1")

    return quarter_dates[quarter]


class VATService:
    """Service voor BTW berekeningen en aangiftes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_vat(self, company_id: uuid.UUID, period: str) -> dict:
        """Bereken BTW voor een periode."""
        start_date, end_date = parse_period(period)

        # BTW ontvangen (op omzet)
        collected_q = select(
            func.coalesce(func.sum(Transaction.btw_amount), 0)
        ).where(
            Transaction.company_id == company_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.status.in_([TransactionStatus.PROCESSED, TransactionStatus.REVIEWED]),
        )

        # BTW betaald (op kosten)
        paid_q = select(
            func.coalesce(func.sum(Transaction.btw_amount), 0)
        ).where(
            Transaction.company_id == company_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.status.in_([TransactionStatus.PROCESSED, TransactionStatus.REVIEWED]),
        )

        # BTW verdeling per tarief
        breakdown_q = select(
            Transaction.btw_percentage,
            Transaction.type,
            func.sum(Transaction.btw_amount).label("total_btw"),
            func.count().label("count"),
        ).where(
            Transaction.company_id == company_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.status.in_([TransactionStatus.PROCESSED, TransactionStatus.REVIEWED]),
        ).group_by(Transaction.btw_percentage, Transaction.type)

        collected = Decimal(str((await self.db.execute(collected_q)).scalar() or 0))
        paid = Decimal(str((await self.db.execute(paid_q)).scalar() or 0))
        balance = collected - paid

        breakdown_result = await self.db.execute(breakdown_q)
        breakdown = [
            {
                "btw_percentage": float(row.btw_percentage or 0),
                "type": row.type,
                "total_btw": float(row.total_btw or 0),
                "count": row.count,
            }
            for row in breakdown_result.all()
        ]

        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "btw_collected": collected,
            "btw_paid": paid,
            "btw_balance": balance,
            "breakdown": breakdown,
        }

    async def generate_report(self, company_id: uuid.UUID, period: str) -> VATReport:
        """Genereer een BTW aangifte rapport."""
        calculation = await self.calculate_vat(company_id, period)
        start_date, end_date = parse_period(period)

        report = VATReport(
            id=uuid.uuid4(),
            company_id=company_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            btw_collected=calculation["btw_collected"],
            btw_paid=calculation["btw_paid"],
            btw_balance=calculation["btw_balance"],
            status=VATStatus.DRAFT,
        )
        self.db.add(report)
        return report
