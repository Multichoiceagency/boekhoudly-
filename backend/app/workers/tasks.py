import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper om async functies in Celery tasks te draaien."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """Verwerk een geüpload document: OCR -> AI classificatie -> grootboekregels."""
    from app.database import async_session
    from app.models.document import Document, ProcessingStatus
    from app.models.transaction import Transaction, TransactionType, TransactionSource, TransactionStatus
    from app.services.ocr_service import OCRService
    from app.services.ai_classifier import AIClassifierService
    from app.services.ledger_service import LedgerService
    from app.services.storage_service import StorageService
    from sqlalchemy import select
    from decimal import Decimal
    from datetime import date
    import uuid

    async def _process():
        async with async_session() as db:
            # Haal document op
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document {document_id} niet gevonden")
                return

            try:
                # Stap 1: OCR
                doc.processing_status = ProcessingStatus.OCR_PROCESSING
                await db.commit()

                storage = StorageService()
                file_content = await storage.get_file(doc.file_url.split("/")[-1])

                ocr = OCRService()
                text = await ocr.extract_text(file_content, doc.file_type)
                doc.ocr_text = text

                # Parse factuurgegevens
                invoice_data = ocr.parse_invoice_data(text)
                doc.extracted_data = invoice_data

                # Stap 2: AI classificatie
                doc.processing_status = ProcessingStatus.AI_PROCESSING
                await db.commit()

                classifier = AIClassifierService()
                description = invoice_data.get("vendor", "") or text[:200]
                amount = invoice_data.get("amount", 0) or 0

                classification = await classifier.classify_transaction(description, amount)

                # Stap 3: Maak transactie aan
                btw_pct = Decimal(str(classification.get("btw_percentage", 21)))
                tx_amount = Decimal(str(amount))
                btw_amount = tx_amount * btw_pct / Decimal("100")

                transaction = Transaction(
                    id=uuid.uuid4(),
                    company_id=doc.company_id,
                    amount=tx_amount,
                    date=date.today(),
                    description=description,
                    type=TransactionType(classification.get("type", "expense")),
                    category=classification.get("category", "Overige kosten"),
                    btw_percentage=btw_pct,
                    btw_amount=btw_amount,
                    source=TransactionSource.PDF,
                    status=TransactionStatus.PROCESSED,
                    confidence_score=classification.get("confidence_score", 0.5),
                    ai_category=classification.get("category"),
                )
                db.add(transaction)
                await db.flush()

                # Stap 4: Grootboekregels
                ledger = LedgerService(db)
                await ledger.create_entries(transaction)

                doc.processing_status = ProcessingStatus.COMPLETED
                await db.commit()

                logger.info(f"Document {document_id} succesvol verwerkt")

            except Exception as e:
                doc.processing_status = ProcessingStatus.ERROR
                await db.commit()
                logger.error(f"Fout bij verwerken document {document_id}: {e}")
                raise self.retry(exc=e, countdown=60)

    run_async(_process())


@celery_app.task
def calculate_vat_report(company_id: str, period: str):
    """Bereken en genereer een BTW rapport."""
    from app.database import async_session
    from app.services.vat_service import VATService
    import uuid

    async def _calculate():
        async with async_session() as db:
            vat_service = VATService(db)
            report = await vat_service.generate_report(uuid.UUID(company_id), period)
            await db.commit()
            logger.info(f"BTW rapport gegenereerd voor {company_id}, periode {period}")

    run_async(_calculate())
