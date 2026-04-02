from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    company_id: UUID
    file_url: str
    file_name: str
    file_type: str
    extracted_data: dict | None = None
    processing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentProcessingStatus(BaseModel):
    document_id: UUID
    status: str
    progress: int = 0
    message: str | None = None
