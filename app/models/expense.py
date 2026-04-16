import uuid
from datetime import datetime, date
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, Text
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Overig")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    btw_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=21)
    status: Mapped[str] = mapped_column(String(20), default="concept")  # concept, geboekt, review
    supplier_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="expenses")
