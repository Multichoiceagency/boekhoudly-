import uuid
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, ForeignKey, Text
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    client: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    lines: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), default="concept")  # concept, verzonden, betaald, verlopen
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="invoices")
