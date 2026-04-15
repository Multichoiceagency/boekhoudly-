import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class IntegrationConnection(Base):
    """Per-company connection to an external CRM/accounting platform.

    Each company can have one connection per provider. Credentials are stored
    as JSONB so each provider can have its own auth shape (api_key, oauth tokens,
    administration_id, etc.).
    """
    __tablename__ = "integration_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credentials: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_integration_company_provider", "company_id", "provider", unique=True),
    )
