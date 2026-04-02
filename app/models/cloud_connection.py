import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer
from app.models.compat import GUID as UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CloudConnection(Base):
    __tablename__ = "cloud_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable=False)

    # Provider info
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google_drive, dropbox, onedrive
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # OAuth tokens (encrypted in production)
    access_token: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Sync settings
    sync_folder_id: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Remote folder ID to watch
    sync_folder_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    auto_import: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-import new documents

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, expired, revoked, error
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    files_imported: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", backref="cloud_connections")
    user = relationship("User", backref="cloud_connections")
