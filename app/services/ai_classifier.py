import logging
import json
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CLASSIFICATION_PROMPT = """Je bent een ervaren Nederlandse boekhouder. Classificeer de volgende transactie.

Transactie:
- Omschrijving: {description}
- Bedrag: €{amount}

Geef je antwoord als JSON met exact deze velden:
{{
    "category": "categorie naam",
    "btw_percentage": 21,
    "type": "income" of "expense",
    "confidence_score": 0.95,
    "explanation": "korte uitleg"
}}

Mogelijke categorieën:
- Omzet (income)
- Marketing & Reclame
- Software & Licenties
- Kantoorkosten
- Transport & Reizen
- Verzekeringen
- Telefoon & Internet
- Huur & Huisvesting
- Personeel & Salaris
- Advieskosten
- Afschrijvingen
- Overige kosten

BTW percentages: 21% (standaard), 9% (laag tarief), 0% (vrijgesteld)

Wees precies en geef een realistisch confidence_score tussen 0.0 en 1.0."""

CHAT_PROMPT = """Je bent FiscalFlow AI, een slimme boekhouding-assistent voor Nederlandse ondernemers.
Je helpt met vragen over boekhouding, BTW, belastingen en financieel beheer.
Antwoord altijd in het Nederlands, bondig en praktisch.
Als je het antwoord niet zeker weet, zeg dat eerlijk.

Gebruiker vraagt: {message}"""


class AIClassifierService:
    """AI-service voor het classificeren van transacties en beantwoorden van vragen."""

    async def classify_transaction(self, description: str, amount: float) -> dict:
        """Classificeer een transactie met AI."""
        prompt = CLASSIFICATION_PROMPT.format(description=description, amount=amount)

        # Try OpenAI first, then Anthropic, then fallback
        if settings.OPENAI_API_KEY:
            return await self._classify_openai(prompt)
        elif settings.ANTHROPIC_API_KEY:
            return await self._classify_anthropic(prompt)
        else:
            return self._classify_fallback(description, amount)

    async def _classify_openai(self, prompt: str) -> dict:
        """Classificeer via OpenAI API."""
        try:
            import openai

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI classificatie fout: {e}")
            return self._classify_fallback("", 0)

    async def _classify_anthropic(self, prompt: str) -> dict:
        """Classificeer via Anthropic API."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return self._classify_fallback("", 0)
        except Exception as e:
            logger.error(f"Anthropic classificatie fout: {e}")
            return self._classify_fallback("", 0)

    def _classify_fallback(self, description: str, amount: float) -> dict:
        """Eenvoudige regel-gebaseerde classificatie als fallback."""
        desc_lower = description.lower()

        category_rules = {
            "Marketing & Reclame": ["facebook", "google ads", "advertentie", "marketing", "reclame"],
            "Software & Licenties": ["software", "saas", "licentie", "abonnement", "github", "aws", "hosting"],
            "Kantoorkosten": ["kantoor", "pennen", "papier", "printer", "bureau"],
            "Transport & Reizen": ["trein", "ns", "benzine", "parkeren", "ov", "uber", "taxi", "vlucht"],
            "Verzekeringen": ["verzekering", "polis"],
            "Telefoon & Internet": ["telefoon", "internet", "mobiel", "kpn", "vodafone", "t-mobile"],
            "Huur & Huisvesting": ["huur", "gas", "water", "elektra", "energie"],
            "Personeel & Salaris": ["salaris", "loon", "personeel"],
        }

        category = "Overige kosten"
        for cat, keywords in category_rules.items():
            if any(kw in desc_lower for kw in keywords):
                category = cat
                break

        tx_type = "income" if amount > 0 else "expense"

        return {
            "category": category,
            "btw_percentage": 21.0,
            "type": tx_type,
            "confidence_score": 0.6,
            "explanation": f"Automatisch geclassificeerd als '{category}' op basis van sleutelwoorden.",
        }

    async def chat(self, message: str) -> str:
        """Beantwoord een boekhoudkundige vraag."""
        prompt = CHAT_PROMPT.format(message=message)

        if settings.OPENAI_API_KEY:
            try:
                import openai

                client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI chat fout: {e}")

        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            except Exception as e:
                logger.error(f"Anthropic chat fout: {e}")

        return (
            "Op dit moment is de AI-assistent niet beschikbaar. "
            "Configureer een OpenAI of Anthropic API key om deze functie te gebruiken."
        )
