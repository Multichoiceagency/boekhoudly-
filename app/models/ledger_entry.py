import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("transactions.id"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(10), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="ledger_entries")
