import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)

    # GoCardless fields
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "ING_INGBNL2A"
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requisition_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Account info (populated after user completes bank auth)
    account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, linked, expired, error
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="bank_connections")
