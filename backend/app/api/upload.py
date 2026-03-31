import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.document import Document, ProcessingStatus
from app.schemas.document import DocumentResponse, DocumentProcessingStatus
from app.utils.auth import get_current_user
from app.services.storage_service import StorageService

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "image/jpeg": "jpg",
    "image/png": "png",
}


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload een document voor verwerking."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Bestandstype niet ondersteund. Toegestaan: PDF, CSV, XLSX, JPG, PNG",
        )

    storage = StorageService()
    file_ext = ALLOWED_TYPES[file.content_type]
    file_name = f"{uuid.uuid4()}.{file_ext}"

    content = await file.read()
    file_url = await storage.upload_file(content, file_name)

    document = Document(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        file_url=file_url,
        file_name=file.filename or file_name,
        file_type=file_ext,
        processing_status=ProcessingStatus.UPLOADED,
    )
    db.add(document)
    await db.flush()

    # TODO: Trigger Celery task for async processing
    # process_document.delay(str(document.id))

    return document


@router.get("/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_processing_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal de verwerkingsstatus van een document op."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document niet gevonden")

    progress_map = {
        ProcessingStatus.UPLOADED: 10,
        ProcessingStatus.OCR_PROCESSING: 40,
        ProcessingStatus.AI_PROCESSING: 70,
        ProcessingStatus.COMPLETED: 100,
        ProcessingStatus.ERROR: 0,
    }

    messages = {
        ProcessingStatus.UPLOADED: "Document geüpload, wacht op verwerking...",
        ProcessingStatus.OCR_PROCESSING: "Tekst wordt geëxtraheerd (OCR)...",
        ProcessingStatus.AI_PROCESSING: "AI classificeert transacties...",
        ProcessingStatus.COMPLETED: "Verwerking voltooid!",
        ProcessingStatus.ERROR: "Er is een fout opgetreden bij de verwerking.",
    }

    return DocumentProcessingStatus(
        document_id=doc.id,
        status=doc.processing_status.value,
        progress=progress_map.get(doc.processing_status, 0),
        message=messages.get(doc.processing_status, ""),
    )
