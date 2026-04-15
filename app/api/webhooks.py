import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.webhook_event import WebhookEvent
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


def _verify_signature(raw_body: bytes, signature: str | None, secret: str) -> bool:
    if not secret:
        return True
    if not signature:
        return False
    sig = signature.strip()
    if sig.startswith("sha256="):
        sig = sig[7:]
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


@router.get("/snelstart")
async def snelstart_health():
    """Health check endpoint SnelStart can ping to verify the webhook URL is live."""
    return {"status": "ok", "service": "fiscaalflow", "webhook": "snelstart"}


@router.post("/snelstart")
async def snelstart_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive webhook events from SnelStart.

    Headers supported:
      - X-SnelStart-Signature: optional HMAC-SHA256 signature of the raw body
      - X-SnelStart-Event: event type (e.g. invoice.created, payment.received)
      - X-SnelStart-Event-Id: unique event ID for idempotency
    """
    raw_body = await request.body()

    try:
        payload = await request.json()
    except Exception:
        logger.error("SnelStart webhook: invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    signature = request.headers.get("X-SnelStart-Signature")
    event_type = request.headers.get("X-SnelStart-Event") or payload.get("event_type") or payload.get("type")
    event_id = request.headers.get("X-SnelStart-Event-Id") or payload.get("id") or payload.get("event_id")

    secret = getattr(settings, "SNELSTART_WEBHOOK_SECRET", "")
    valid = _verify_signature(raw_body, signature, secret)

    if secret and not valid:
        logger.warning(f"SnelStart webhook: invalid signature for event {event_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    if event_id:
        existing = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.source == "snelstart",
                WebhookEvent.event_id == event_id,
            )
        )
        if existing.scalar_one_or_none():
            logger.info(f"SnelStart webhook: duplicate event {event_id} ignored")
            return {"status": "duplicate", "event_id": event_id}

    event = WebhookEvent(
        source="snelstart",
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        signature=signature,
        signature_valid=valid,
        processed=False,
    )
    db.add(event)
    await db.flush()

    logger.info(f"SnelStart webhook received: type={event_type} id={event_id}")

    return {"status": "received", "event_id": event_id, "event_type": event_type}
