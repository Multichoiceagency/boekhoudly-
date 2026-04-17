"""Uitstel van betaling — Belastingdienst formulier OV1352.

Endpoints to pre-fill, AI-generate the reason letter, and export
the payment arrangement request form.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.services.ai_classifier import AIClassifierService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uitstel", tags=["Uitstel"])

UITSTEL_AI_PROMPT = """Je bent een ervaren Nederlands belastingadviseur. Schrijf een professionele,
zakelijke motivatiebrief voor een verzoek om uitstel van betaling bij de Belastingdienst.

Bedrijfsgegevens:
- Naam: {company_name}
- KvK: {kvk}
- Branche: {industry}

Belastingschuld:
- Belastingsoort: {tax_type}
- Aanslagnummer: {assessment_number}
- Openstaand bedrag: €{amount}
- Reden: {reason}

Voorstel:
- Maandelijks bedrag: €{monthly_amount}
- Aantal termijnen: {num_terms}

Schrijf de motivatiebrief in maximaal 150 woorden. Toon begrip, wees concreet over de
financiële situatie en het herstelplan. Eindig positief. Alleen de brieftekst, geen
aanhef of ondertekening — die staan al op het formulier.
"""


@router.get("/prefill")
async def prefill_form(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pre-fill the uitstel form from the user's company data."""
    company = None
    if current_user.company_id:
        result = await db.execute(select(Company).where(Company.id == current_user.company_id))
        company = result.scalar_one_or_none()

    # Fallback for admin / users without company_id: pick the first company in the system
    if not company:
        result = await db.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()

    return {
        "company_name": company.name if company else "",
        "kvk_number": company.kvk_number if company else "",
        "btw_number": company.btw_number if company else "",
        "address": company.address if company else "",
        "postal_code": company.postal_code if company else "",
        "city": company.city if company else "",
        "iban": company.iban if company else "",
        "phone": company.phone if company else "",
        "industry": company.industry if company else "",
        "contact_name": current_user.full_name or "",
        "contact_email": current_user.email or "",
    }


@router.post("/generate-reason")
async def generate_reason(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """Use AI to generate a professional Dutch motivation letter for the payment arrangement request."""
    prompt = UITSTEL_AI_PROMPT.format(
        company_name=data.get("company_name", ""),
        kvk=data.get("kvk_number", ""),
        industry=data.get("industry", ""),
        tax_type=data.get("tax_type", "Omzetbelasting"),
        assessment_number=data.get("assessment_number", ""),
        amount=data.get("amount", "0"),
        reason=data.get("reason_summary", "tijdelijke liquiditeitskrapte"),
        monthly_amount=data.get("monthly_amount", "0"),
        num_terms=data.get("num_terms", "12"),
    )

    try:
        ai = AIClassifierService()
        letter = await ai.chat(prompt)
        return {"letter": letter}
    except Exception as e:
        logger.warning(f"AI generation failed: {e}")
        return {
            "letter": (
                f"Hierbij verzoek ik om een betalingsregeling voor de openstaande "
                f"belastingschuld van €{data.get('amount', '0')} ({data.get('tax_type', 'belasting')}). "
                f"Door tijdelijke liquiditeitskrapte ben ik niet in staat het volledige bedrag "
                f"in één keer te voldoen. Ik stel voor om maandelijks €{data.get('monthly_amount', '0')} "
                f"af te lossen in {data.get('num_terms', '12')} termijnen. "
                f"Ik verwacht dat de financiële situatie binnen deze periode zal verbeteren."
            )
        }
