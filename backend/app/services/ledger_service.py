import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Transaction, TransactionType
from app.models.ledger_entry import LedgerEntry

# Nederlands rekeningschema (simplified)
CHART_OF_ACCOUNTS = {
    # Balansrekeningen
    "1000": "Kas",
    "1100": "Bank",
    "1300": "Debiteuren",
    "1600": "Crediteuren",
    "1500": "BTW te vorderen",
    "1510": "BTW af te dragen",
    # Kostenrekeningen
    "4000": "Omzet",
    "4100": "Omzet diensten",
    "6000": "Inkoopkosten",
    "6100": "Marketing & Reclame",
    "6200": "Software & Licenties",
    "6300": "Kantoorkosten",
    "6400": "Transport & Reizen",
    "6500": "Verzekeringen",
    "6600": "Telefoon & Internet",
    "6700": "Huur & Huisvesting",
    "6800": "Personeel & Salaris",
    "6900": "Advieskosten",
    "7000": "Afschrijvingen",
    "7999": "Overige kosten",
}

CATEGORY_TO_ACCOUNT = {
    "Omzet": "4000",
    "Omzet diensten": "4100",
    "Inkoopkosten": "6000",
    "Marketing & Reclame": "6100",
    "Software & Licenties": "6200",
    "Kantoorkosten": "6300",
    "Transport & Reizen": "6400",
    "Verzekeringen": "6500",
    "Telefoon & Internet": "6600",
    "Huur & Huisvesting": "6700",
    "Personeel & Salaris": "6800",
    "Advieskosten": "6900",
    "Afschrijvingen": "7000",
    "Overige kosten": "7999",
}


class LedgerService:
    """Service voor het aanmaken van grootboekregels (dubbel boekhouden)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entries(self, transaction: Transaction) -> list[LedgerEntry]:
        """Maak grootboekregels aan voor een transactie (dubbel boekhouden)."""
        entries = []
        category = transaction.category or "Overige kosten"
        account_code = CATEGORY_TO_ACCOUNT.get(category, "7999")
        account_name = CHART_OF_ACCOUNTS.get(account_code, "Overige kosten")
        amount = abs(transaction.amount)
        btw_amount = transaction.btw_amount or Decimal("0")
        net_amount = amount - btw_amount

        if transaction.type == TransactionType.EXPENSE:
            # Kosten: debet op kostenrekening, credit op bank
            entries.append(
                LedgerEntry(
                    id=uuid.uuid4(),
                    company_id=transaction.company_id,
                    transaction_id=transaction.id,
                    account_code=account_code,
                    account_name=account_name,
                    debit=net_amount,
                    credit=Decimal("0"),
                    description=transaction.description,
                    date=transaction.date,
                )
            )
            # BTW te vorderen
            if btw_amount > 0:
                entries.append(
                    LedgerEntry(
                        id=uuid.uuid4(),
                        company_id=transaction.company_id,
                        transaction_id=transaction.id,
                        account_code="1500",
                        account_name="BTW te vorderen",
                        debit=btw_amount,
                        credit=Decimal("0"),
                        description=f"BTW {transaction.description}",
                        date=transaction.date,
                    )
                )
            # Credit bank
            entries.append(
                LedgerEntry(
                    id=uuid.uuid4(),
                    company_id=transaction.company_id,
                    transaction_id=transaction.id,
                    account_code="1100",
                    account_name="Bank",
                    debit=Decimal("0"),
                    credit=amount,
                    description=transaction.description,
                    date=transaction.date,
                )
            )
        else:
            # Omzet: debet op bank, credit op omzetrekening
            entries.append(
                LedgerEntry(
                    id=uuid.uuid4(),
                    company_id=transaction.company_id,
                    transaction_id=transaction.id,
                    account_code="1100",
                    account_name="Bank",
                    debit=amount,
                    credit=Decimal("0"),
                    description=transaction.description,
                    date=transaction.date,
                )
            )
            # Credit omzet
            entries.append(
                LedgerEntry(
                    id=uuid.uuid4(),
                    company_id=transaction.company_id,
                    transaction_id=transaction.id,
                    account_code=account_code,
                    account_name=account_name,
                    debit=Decimal("0"),
                    credit=net_amount,
                    description=transaction.description,
                    date=transaction.date,
                )
            )
            # BTW af te dragen
            if btw_amount > 0:
                entries.append(
                    LedgerEntry(
                        id=uuid.uuid4(),
                        company_id=transaction.company_id,
                        transaction_id=transaction.id,
                        account_code="1510",
                        account_name="BTW af te dragen",
                        debit=Decimal("0"),
                        credit=btw_amount,
                        description=f"BTW {transaction.description}",
                        date=transaction.date,
                    )
                )

        for entry in entries:
            self.db.add(entry)

        return entries

    async def get_trial_balance(
        self, company_id: uuid.UUID, start: date | None = None, end: date | None = None
    ) -> list[dict]:
        """Haal de proefbalans op."""
        from sqlalchemy import func

        query = select(
            LedgerEntry.account_code,
            LedgerEntry.account_name,
            func.sum(LedgerEntry.debit).label("total_debit"),
            func.sum(LedgerEntry.credit).label("total_credit"),
        ).where(LedgerEntry.company_id == company_id)

        if start:
            query = query.where(LedgerEntry.date >= start)
        if end:
            query = query.where(LedgerEntry.date <= end)

        query = query.group_by(LedgerEntry.account_code, LedgerEntry.account_name)
        query = query.order_by(LedgerEntry.account_code)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "account_code": row.account_code,
                "account_name": row.account_name,
                "debit": row.total_debit or Decimal("0"),
                "credit": row.total_credit or Decimal("0"),
                "balance": (row.total_debit or Decimal("0")) - (row.total_credit or Decimal("0")),
            }
            for row in rows
        ]
