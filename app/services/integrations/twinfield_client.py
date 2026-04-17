"""Twinfield client — OAuth2 + SOAP based.

Twinfield's API is genuinely complex (cluster discovery, OAuth2 token
refresh, SOAP/XBRL responses). For now this client only validates that
all required credentials are present. Full data-fetching can be added
later when the OAuth flow is wired up.

Docs: https://accounting.twinfield.com/webservices/documentation
"""
import httpx
from app.services.integrations.base import IntegrationClient

ACCESS_TOKEN_URL = "https://login.twinfield.com/auth/authentication/connect/token"


class TwinfieldClient(IntegrationClient):
    PROVIDER = "twinfield"

    async def test_connection(self) -> dict:
        required = ["client_id", "client_secret", "refresh_token"]
        missing = [k for k in required if not self.credentials.get(k)]
        if missing:
            return {"status": "error", "message": f"Ontbrekend: {', '.join(missing)}"}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    ACCESS_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.credentials["client_id"],
                        "client_secret": self.credentials["client_secret"],
                        "refresh_token": self.credentials["refresh_token"],
                    },
                )
            if r.status_code == 200:
                token_data = r.json()
                return {
                    "status": "connected",
                    "message": "Twinfield OAuth refresh werkt — data-koppeling is nog in ontwikkeling",
                    "metadata": {
                        "expires_in": token_data.get("expires_in"),
                        "scope": token_data.get("scope"),
                    },
                }
            return {"status": "error", "message": f"Twinfield token endpoint HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        raise NotImplementedError("Twinfield data-sync wordt binnenkort ondersteund")

    async def list_invoices(self) -> list[dict]:
        raise NotImplementedError("Twinfield data-sync wordt binnenkort ondersteund")

    async def list_payments(self) -> list[dict]:
        raise NotImplementedError("Twinfield data-sync wordt binnenkort ondersteund")
