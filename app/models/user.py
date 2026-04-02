import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Text
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # nullable for OAuth users
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("companies.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # 'admin', 'accountant', 'user'

    # OAuth fields
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'google', null for email
    oauth_provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Google sub ID
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Onboarding tracking
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(default=0)  # 0-5
    onboarding_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Store partial onboarding data

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="users")
