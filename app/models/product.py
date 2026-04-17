import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, ForeignKey
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Product(Base):
    """Reusable product/service catalog item for invoices and quotes."""
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    btw_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=21)
    unit: Mapped[str] = mapped_column(String(20), default="stuk")  # stuk, uur, maand, project, km
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", backref="products")
