import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kvk_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    btw_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # New fields
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # zzp, bv, vof, eenmanszaak
    fiscal_year_start: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "01-01"
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # "#059669"
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="company")
    transactions = relationship("Transaction", back_populates="company")
    documents = relationship("Document", back_populates="company")
    vat_reports = relationship("VATReport", back_populates="company")
