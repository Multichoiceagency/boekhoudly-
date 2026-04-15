import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, Index
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CompanySubscription(Base):
    __tablename__ = "company_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False, unique=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("subscription_plans.id"), nullable=False)
    accountant_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)

    # Per-company overrides (null = inherit from plan)
    monthly_eur_override: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Current billing period (rolled monthly)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Running counters for the current period
    ai_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_cost_eur_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, paused, cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_subscription_accountant", "accountant_id"),
    )
