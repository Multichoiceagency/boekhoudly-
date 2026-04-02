import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Debtor(Base):
    __tablename__ = "debtors"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kvk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    btw: Mapped[str | None] = mapped_column(String(30), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    payment_term: Mapped[int] = mapped_column(Integer, default=30)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="debtors")
