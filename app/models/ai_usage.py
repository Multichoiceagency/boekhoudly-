import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index
from app.models.compat import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AiUsage(Base):
    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)  # 'chat', 'classify', 'extract', 'ocr'
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cost_eur_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ai_usage_company_date", "company_id", "created_at"),
    )
