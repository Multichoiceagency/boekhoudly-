import uuid
import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class VATStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"


class VATReport(Base):
    __tablename__ = "vat_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    btw_collected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    btw_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    btw_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[VATStatus] = mapped_column(Enum(VATStatus), default=VATStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="vat_reports")
