import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Index, ForeignKey
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CrmRecord(Base):
    """Cached records from external CRM systems (Perfex, Moneybird, etc.)."""
    __tablename__ = "crm_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("companies.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_crm_lookup", "provider", "resource", "external_id"),
        Index("ix_crm_company_resource", "company_id", "resource"),
    )


class CrmSyncRun(Base):
    """One row per sync attempt — used to show 'last synced' in the UI."""
    __tablename__ = "crm_sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("companies.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    counts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
