import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


async def _build_data_context(user: User, db: AsyncSession) -> str:
    """Build a rich data context string from the user's workspace for AI enrichment."""
    from app.models.invoice import Invoice
    from app.models.expense import Expense
    from app.models.debtor import Debtor
    from app.models.company import Company

    ctx_parts = []

    # Company info
    if user.company_id:
        comp_result = await db.execute(select(Company).where(Company.id == user.company_id))
        comp = comp_result.scalar_one_or_none()
        if comp:
            ctx_parts.append(f"Bedrijf: {comp.name} (KvK: {comp.kvk_number or '-'}, BTW: {comp.btw_number or '-'})")

    # Invoices summary
    cid = user.company_id
    if cid:
        inv_q = select(Invoice).where(Invoice.company_id == cid)
    else:
        inv_q = select(Invoice)

    inv_result = await db.execute(inv_q)
    invoices = inv_result.scalars().all()

    if invoices:
        total_rev = sum(sum(l.get("qty", 0) * l.get("price", 0) for l in (i.lines or [])) for i in invoices if getattr(i, 'document_type', 'factuur') == 'factuur')
        total_btw = sum(sum(l.get("qty", 0) * l.get("price", 0) * l.get("btwRate", 0) / 100 for l in (i.lines or [])) for i in invoices if getattr(i, 'document_type', 'factuur') == 'factuur')
        betaald = [i for i in invoices if i.status == 'betaald' and getattr(i, 'document_type', 'factuur') == 'factuur']
        verzonden = [i for i in invoices if i.status == 'verzonden' and getattr(i, 'document_type', 'factuur') == 'factuur']
        verlopen = [i for i in invoices if i.status == 'verlopen' and getattr(i, 'document_type', 'factuur') == 'factuur']
        offertes = [i for i in invoices if getattr(i, 'document_type', None) == 'offerte']
        creditnotas = [i for i in invoices if getattr(i, 'document_type', None) == 'creditnota']

        ctx_parts.append(f"\nFACTUREN ({len([i for i in invoices if getattr(i, 'document_type', 'factuur') == 'factuur'])} totaal):")
        ctx_parts.append(f"- Totale omzet (excl BTW): €{total_rev:,.2f}")
        ctx_parts.append(f"- Totale BTW gefactureerd: €{total_btw:,.2f}")
        ctx_parts.append(f"- Betaald: {len(betaald)} facturen")
        ctx_parts.append(f"- Openstaand/verzonden: {len(verzonden)} facturen")
        ctx_parts.append(f"- Verlopen: {len(verlopen)} facturen")
        if offertes:
            ctx_parts.append(f"- Offertes: {len(offertes)}")
        if creditnotas:
            ctx_parts.append(f"- Creditnota's: {len(creditnotas)}")

        # Top 5 recent invoices
        recent = sorted([i for i in invoices if getattr(i, 'document_type', 'factuur') == 'factuur'], key=lambda x: str(x.date), reverse=True)[:5]
        if recent:
            ctx_parts.append("\nRecente facturen:")
            for inv in recent:
                total = sum(l.get("qty", 0) * l.get("price", 0) * (1 + l.get("btwRate", 0) / 100) for l in (inv.lines or []))
                ctx_parts.append(f"  {inv.number} — {inv.client} — €{total:,.2f} — {inv.status} — {inv.date}")

        # Top 5 overdue
        if verlopen:
            ctx_parts.append(f"\nVerlopen facturen ({len(verlopen)}):")
            for inv in verlopen[:5]:
                total = sum(l.get("qty", 0) * l.get("price", 0) * (1 + l.get("btwRate", 0) / 100) for l in (inv.lines or []))
                ctx_parts.append(f"  {inv.number} — {inv.client} — €{total:,.2f} — vervallen {inv.due_date}")

    # Expenses
    if cid:
        exp_q = select(Expense).where(Expense.company_id == cid)
    else:
        exp_q = select(Expense)
    exp_result = await db.execute(exp_q)
    expenses = exp_result.scalars().all()
    if expenses:
        total_exp = sum(float(e.amount) for e in expenses)
        ctx_parts.append(f"\nUITGAVEN ({len(expenses)} totaal): €{total_exp:,.2f}")

    # Debtors
    if cid:
        deb_q = select(Debtor).where(Debtor.company_id == cid)
    else:
        deb_q = select(Debtor)
    deb_result = await db.execute(deb_q)
    debtors = deb_result.scalars().all()
    if debtors:
        ctx_parts.append(f"\nKLANTEN/DEBITEUREN: {len(debtors)} totaal")
        for d in debtors[:10]:
            ctx_parts.append(f"  {d.name} ({d.city or '-'})")

    if not ctx_parts:
        return "Geen bedrijfsdata beschikbaar — het bedrijf heeft nog geen facturen, uitgaven of klanten."

    return "\n".join(ctx_parts)


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stel een boekhoudkundige vraag aan de AI — verrijkt met echte bedrijfsdata."""
    # Build data context from the user's actual workspace
    try:
        data_context = await _build_data_context(current_user, db)
    except Exception as e:
        logger.warning(f"Failed to build data context: {e}")
        data_context = "Bedrijfsdata kon niet worden geladen."

    enriched_message = f"""De gebruiker stelt een vraag over hun boekhouding. Gebruik de onderstaande ECHTE bedrijfsdata
om een concreet, specifiek antwoord te geven met echte cijfers. Verwijs naar specifieke facturen,
klanten of bedragen waar relevant. Geef geen generieke antwoorden — gebruik de data.

=== BEDRIJFSDATA ===
{data_context}
=== EINDE DATA ===

Vraag van de gebruiker: {data.message}"""

    classifier = AIClassifierService()
    reply = await classifier.chat(enriched_message)
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
        "groq_configured": bool(settings.GROQ_API_KEY),
        "groq_model": settings.GROQ_MODEL,
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
