"""Uitstel aangifte inkomstenbelasting — Belastingdienst formulier IB 104.

Prefill endpoint + AI-gegenereerde motivatie voor als uitstel > 4 maanden
wordt gevraagd. Het gegenereerde PDF bestand wordt frontend-side gemaakt
in `usePdfTemplates.ts`.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.services.ai_classifier import AIClassifierService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uitstel", tags=["Uitstel"])

UITSTEL_AI_PROMPT = """Je bent een ervaren Nederlands belastingadviseur. Schrijf een korte,
zakelijke motivatie voor een verzoek om uitstel van de aangifte inkomstenbelasting
LANGER dan 4 maanden. Richt je op de Belastingdienst.

Gegevens:
- Naam aanvrager: {naam}
- Aangiftejaar: {aangiftejaar}
- Gevraagd uitstel tot: {tot_datum}
- Reden: {reden}

Houd het onder de 120 woorden. Wees concreet en zakelijk. Geen aanhef
("Geachte heer/mevrouw"), geen ondertekening — alleen de lopende tekst
die in het motivatievak van het formulier past.
"""


@router.get("/prefill")
async def prefill_form(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pre-fill the IB 104 form from the user's profile + active company."""
    company = None
    if current_user.company_id:
        result = await db.execute(select(Company).where(Company.id == current_user.company_id))
        company = result.scalar_one_or_none()

    # Split "Postcode en woonplaats" from Company.postal_code / city for convenience.
    postal_code = (company.postal_code if company else "") or ""
    city = (company.city if company else "") or ""
    address = (company.address if company else "") or ""

    return {
        "naam": current_user.full_name or (company.name if company else ""),
        "adres": address,
        "postcode": postal_code,
        "woonplaats": city,
        "bsn": "",
        "telefoon": (company.phone if company else "") or "",
    }


@router.post("/generate-reason")
async def generate_reason(data: dict):
    """AI-generate a Dutch motivation text for extended (> 4 months) uitstel."""
    prompt = UITSTEL_AI_PROMPT.format(
        naam=data.get("naam", ""),
        aangiftejaar=data.get("aangiftejaar", ""),
        tot_datum=data.get("tot_datum", ""),
        reden=data.get("reden_kort", "tijdelijke omstandigheden"),
    )
    try:
        ai = AIClassifierService()
        letter = await ai.chat(prompt)
        return {"letter": letter.strip()}
    except Exception as e:
        logger.warning(f"AI uitstel-motivatie mislukt: {e}")
        return {
            "letter": (
                "In verband met het wachten op aanvullende administratieve gegevens "
                "van derden (werkgevers, banken, pensioenuitvoerders) is het niet mogelijk "
                "om de aangifte binnen vier maanden volledig en correct in te dienen. "
                "Ik verzoek vriendelijk om uitstel tot de hierboven genoemde datum."
            )
        }
