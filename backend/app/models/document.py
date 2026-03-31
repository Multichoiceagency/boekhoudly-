import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    OCR_PROCESSING = "ocr_processing"
    AI_PROCESSING = "ai_processing"
    COMPLETED = "completed"
    ERROR = "error"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="documents")
