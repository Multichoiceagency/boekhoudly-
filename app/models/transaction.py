import uuid
import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, Float, Date, DateTime, Enum, ForeignKey, Text
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionSource(str, enum.Enum):
    MANUAL = "manual"
    BANK = "bank"
    PDF = "pdf"
    CSV = "csv"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    REVIEWED = "reviewed"
    ERROR = "error"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    btw_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    btw_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    source: Mapped[TransactionSource] = mapped_column(Enum(TransactionSource), default=TransactionSource.MANUAL)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="transactions")
    ledger_entries = relationship("LedgerEntry", back_populates="transaction")
