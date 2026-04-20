import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, async_session
from app.models.user import User
from app.models.document import Document, ProcessingStatus
from app.schemas.document import DocumentResponse, DocumentProcessingStatus
from app.utils.auth import get_current_user
from app.services.storage_service import StorageService
from app.services.ocr_service import OCRService
from app.services.ai_classifier import AIClassifierService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/csv": "csv",
    "application/vnd.ms-excel": "csv",  # sometimes sent for CSV
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "image/jpeg": "jpg",
    "image/png": "png",
}

EXTENSION_FALLBACK = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
}


def _resolve_file_type(content_type: str | None, filename: str | None) -> str | None:
    if content_type and content_type in ALLOWED_TYPES:
        return ALLOWED_TYPES[content_type]
    if filename:
        lower = filename.lower()
        for ext, ft in EXTENSION_FALLBACK.items():
            if lower.endswith(ext):
                return ft
    return None


async def _process_document(document_id: uuid.UUID, content: bytes, file_ext: str):
    """Run OCR/extraction + AI classification on a document and persist the result.

    Designed to run as a FastAPI BackgroundTask — opens its own DB session
    because the request-scoped session is closed by the time this runs.
    """
    ocr = OCRService()
    try:
        text = await ocr.extract_text(content, file_ext)
    except Exception as e:
        logger.exception(f"OCR mislukt voor document {document_id}: {e}")
        text = ""

    extracted = ocr.parse_invoice_data(text) if text else {}

    # AI classification (best effort — don't fail the whole job if it errors)
    ai_result = None
    try:
        if text and extracted.get("amount"):
            ai_result = await AIClassifierService().classify_transaction(
                description=text[:500],
                amount=float(extracted.get("amount") or 0),
            )
    except Exception as e:
        logger.warning(f"AI classificatie mislukt voor {document_id}: {e}")

    async with async_session() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            logger.warning(f"Document {document_id} verdween tijdens verwerking")
            return
        doc.ocr_text = text or None
        doc.extracted_data = {
            **extracted,
            **({"ai": ai_result} if ai_result else {}),
        } or None
        doc.processing_status = (
            ProcessingStatus.COMPLETED if text else ProcessingStatus.ERROR
        )
        await session.commit()
    logger.info(f"Document {document_id} verwerkt (status={doc.processing_status.value})")


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload een document voor verwerking (PDF, CSV, XLSX, JPG, PNG)."""
    file_ext = _resolve_file_type(file.content_type, file.filename)
    if not file_ext:
        raise HTTPException(
            status_code=400,
            detail="Bestandstype niet ondersteund. Toegestaan: PDF, CSV, XLSX, JPG, PNG",
        )

    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Geen bedrijf gekoppeld aan je account")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Bestand is leeg")

    file_name = f"{uuid.uuid4()}.{file_ext}"

    storage = StorageService()
    try:
        file_url = await storage.upload_file(content, file_name)
    except Exception as e:
        logger.error(f"Storage upload mislukt: {e}")
        raise HTTPException(status_code=502, detail="Opslag is niet bereikbaar")

    document = Document(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        file_url=file_url,
        file_name=file.filename or file_name,
        file_type=file_ext,
        processing_status=ProcessingStatus.OCR_PROCESSING,
    )
    db.add(document)
    await db.flush()
    doc_id = document.id

    background_tasks.add_task(_process_document, doc_id, content, file_ext)

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
