import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.services.ai_classifier import AIClassifierService, _pick_provider
from app.services.ai_usage_tracker import track_ai_usage
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/ai", tags=["AI"])
settings = get_settings()


class ClassifyRequest(BaseModel):
    description: str
    amount: float


class ClassifyResponse(BaseModel):
    category: str
    btw_percentage: float
    type: str
    confidence_score: float
    explanation: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    credits_used: int | None = None
    credits_remaining: int | None = None
    over_quota: bool | None = None


class InsightItem(BaseModel):
    title: str
    description: str
    type: str
    priority: str


@router.post("/classify", response_model=ClassifyResponse)
async def classify_transaction(
    data: ClassifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Classificeer een transactie met AI."""
    classifier = AIClassifierService()
    result = await classifier.classify_transaction(data.description, data.amount)
    await track_ai_usage(db, user=current_user, operation="classify")
    return result


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stel een boekhoudkundige vraag aan de AI."""
    classifier = AIClassifierService()
    reply = await classifier.chat(data.message)
    usage = await track_ai_usage(
        db,
        user=current_user,
        operation="chat",
        tokens_in=len(data.message) // 4,
        tokens_out=len(reply) // 4,
    )
    return ChatResponse(
        reply=reply,
        credits_used=usage.get("credits_used"),
        credits_remaining=usage.get("credits_remaining"),
        over_quota=usage.get("over_quota"),
    )


@router.get("/status")
async def ai_status(current_user: User = Depends(get_current_user)):
    """Diagnose: which AI provider is active + Ollama reachability + installed models."""
    provider = _pick_provider()
    out: dict = {
        "active_provider": provider,
        "ai_provider_setting": settings.AI_PROVIDER,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
    }
    if settings.OLLAMA_BASE_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if r.status_code == 200:
                tags = r.json().get("models", [])
                out["ollama_reachable"] = True
                out["ollama_models"] = [m.get("name") for m in tags]
            else:
                out["ollama_reachable"] = False
                out["ollama_error"] = f"HTTP {r.status_code}"
        except Exception as e:
            out["ollama_reachable"] = False
            out["ollama_error"] = str(e)[:200]
    return out


@router.post("/ollama/pull")
async def ollama_pull(data: dict, current_user: User = Depends(get_current_user)):
    """Trigger Ollama to download a model. Streams progress until done.
    Body: {"model": "llama3.2:3b"}. Admin-only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen admins")
    if not settings.OLLAMA_BASE_URL:
        raise HTTPException(status_code=503, detail="OLLAMA_BASE_URL niet ingesteld")

    model = data.get("model") or settings.OLLAMA_MODEL
    try:
        async with httpx.AsyncClient(timeout=900) as client:
            r = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/pull",
                json={"name": model, "stream": False},
            )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Ollama pull HTTP {r.status_code}: {r.text[:200]}")
        return {"status": "pulled", "model": model}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Ollama onbereikbaar: {str(e)[:200]}")


@router.get("/insights", response_model=list[InsightItem])
async def get_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Haal AI-gegenereerde inzichten op voor het dashboard."""
    # For now return mock insights - will be replaced with real AI analysis
    return [
        InsightItem(
            title="BTW aangifte deadline",
            description="Je BTW aangifte voor Q1 2026 moet voor 30 april worden ingediend. Op basis van je transacties is het geschatte bedrag €2.611.",
            type="deadline",
            priority="high",
        ),
        InsightItem(
            title="Ongebruikelijke uitgave gedetecteerd",
            description="Een betaling van €1.250 aan een onbekende leverancier is gemarkeerd voor review.",
            type="alert",
            priority="medium",
        ),
        InsightItem(
            title="Besparingskans",
            description="Je softwarekosten zijn 23% gestegen t.o.v. vorig kwartaal. Overweeg contracten te evalueren.",
            type="tip",
            priority="low",
        ),
    ]
