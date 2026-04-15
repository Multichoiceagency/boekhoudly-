import logging
import json
import httpx
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

CHAT_SYSTEM_PROMPT = """Je bent FiscalFlow AI, een slimme boekhouding-assistent voor Nederlandse ondernemers.
Je helpt met vragen over boekhouding, BTW, belastingen en financieel beheer.
Antwoord altijd in het Nederlands, bondig en praktisch.
Als je het antwoord niet zeker weet, zeg dat eerlijk."""


def _pick_provider() -> str:
    """Pick AI provider based on AI_PROVIDER setting + which credentials are configured."""
    pref = (settings.AI_PROVIDER or "auto").lower()
    if pref != "auto":
        return pref
    # Auto order: Groq (free + fast) → OpenAI → Anthropic → Ollama → fallback
    if settings.GROQ_API_KEY:
        return "groq"
    if settings.OPENAI_API_KEY:
        return "openai"
    if settings.ANTHROPIC_API_KEY:
        return "anthropic"
    if settings.OLLAMA_BASE_URL:
        return "ollama"
    return "fallback"


class AIClassifierService:
    """AI-service voor het classificeren van transacties en beantwoorden van vragen."""

    async def classify_transaction(self, description: str, amount: float) -> dict:
        prompt = CLASSIFICATION_PROMPT.format(description=description, amount=amount)
        provider = _pick_provider()

        try:
            if provider == "groq":
                return await self._classify_groq(prompt)
            if provider == "ollama":
                return await self._classify_ollama(prompt)
            if provider == "openai":
                return await self._classify_openai(prompt)
            if provider == "anthropic":
                return await self._classify_anthropic(prompt)
        except Exception as e:
            logger.warning(f"AI classify via {provider} failed, falling back: {e}")

        return self._classify_fallback(description, amount)

    async def chat(self, message: str) -> str:
        provider = _pick_provider()

        try:
            if provider == "groq":
                return await self._chat_groq(message)
            if provider == "ollama":
                return await self._chat_ollama(message)
            if provider == "openai":
                return await self._chat_openai(message)
            if provider == "anthropic":
                return await self._chat_anthropic(message)
        except Exception as e:
            logger.warning(f"AI chat via {provider} failed: {e}")

        if provider == "fallback":
            return (
                "De AI-assistent is nog niet geconfigureerd. Tip: maak een gratis Groq account aan op "
                "https://console.groq.com/keys en zet `GROQ_API_KEY` als env var. Dit geeft je "
                "snelle inferentie zonder kosten."
            )
        return f"De AI-assistent ({provider}) is tijdelijk niet bereikbaar. Probeer het later opnieuw."

    # ------------------------------------------------------------------
    # Groq (OpenAI-compatible REST API, free tier, LPU acceleration)
    # ------------------------------------------------------------------
    async def _groq_chat_raw(self, messages: list, json_mode: bool = False) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY niet ingesteld")
        body: dict = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "temperature": 0.2 if json_mode else 0.4,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            )
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]

    async def _classify_groq(self, prompt: str) -> dict:
        content = await self._groq_chat_raw(
            [{"role": "user", "content": prompt}],
            json_mode=True,
        )
        try:
            return json.loads(content)
        except Exception:
            start, end = content.find("{"), content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise

    async def _chat_groq(self, message: str) -> str:
        return await self._groq_chat_raw([
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ])

    # ------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------
    async def _ollama_chat_raw(self, messages: list, model: str | None = None, json_mode: bool = False) -> str:
        base = settings.OLLAMA_BASE_URL.rstrip("/")
        if not base:
            raise RuntimeError("OLLAMA_BASE_URL niet ingesteld")
        body: dict = {
            "model": model or settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2 if json_mode else 0.4},
        }
        if json_mode:
            body["format"] = "json"

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{base}/api/chat", json=body)
            r.raise_for_status()
            data = r.json()
        return (data.get("message") or {}).get("content", "")

    async def _classify_ollama(self, prompt: str) -> dict:
        model = settings.OLLAMA_CLASSIFY_MODEL or settings.OLLAMA_MODEL
        content = await self._ollama_chat_raw(
            [{"role": "user", "content": prompt}],
            model=model,
            json_mode=True,
        )
        try:
            return json.loads(content)
        except Exception:
            start, end = content.find("{"), content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise

    async def _chat_ollama(self, message: str) -> str:
        return await self._ollama_chat_raw([
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ])

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    async def _classify_openai(self, prompt: str) -> dict:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    async def _chat_openai(self, message: str) -> str:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------
    async def _classify_anthropic(self, prompt: str) -> dict:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        start, end = content.find("{"), content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        raise ValueError("Anthropic returned no JSON")

    async def _chat_anthropic(self, message: str) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=CHAT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------
    def _classify_fallback(self, description: str, amount: float) -> dict:
        desc_lower = (description or "").lower()
        category_rules = {
            "Marketing & Reclame": ["facebook", "google ads", "advertentie", "marketing", "reclame", "linkedin"],
            "Software & Licenties": ["software", "saas", "licentie", "abonnement", "github", "aws", "hosting", "openai", "anthropic"],
            "Kantoorkosten": ["kantoor", "pennen", "papier", "printer", "bureau"],
            "Transport & Reizen": ["trein", "ns", "benzine", "parkeren", "ov", "uber", "taxi", "vlucht", "shell", "bp"],
            "Verzekeringen": ["verzekering", "polis", "aon", "centraal beheer"],
            "Telefoon & Internet": ["telefoon", "internet", "mobiel", "kpn", "vodafone", "t-mobile", "ziggo"],
            "Huur & Huisvesting": ["huur", "gas", "water", "elektra", "energie", "vattenfall", "essent"],
            "Personeel & Salaris": ["salaris", "loon", "personeel"],
        }
        category = "Overige kosten"
        for cat, keywords in category_rules.items():
            if any(kw in desc_lower for kw in keywords):
                category = cat
                break
        return {
            "category": category,
            "btw_percentage": 21.0,
            "type": "income" if amount > 0 else "expense",
            "confidence_score": 0.6,
            "explanation": f"Automatisch geclassificeerd als '{category}' op basis van sleutelwoorden (geen LLM beschikbaar).",
        }
