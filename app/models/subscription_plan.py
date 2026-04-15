import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, Numeric
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    monthly_eur: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    ai_credits_included: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_overage_eur_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
