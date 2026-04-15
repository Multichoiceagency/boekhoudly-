"""Moneybird REST API v2 client.

Uses a Personal Access Token (Bearer) + administration_id. Tokens can be
created in Moneybird → Profile → Developers → New token.

Docs: https://developer.moneybird.com/
"""
import httpx
from app.services.integrations.base import IntegrationClient

BASE = "https://moneybird.com/api/v2"


class MoneybirdClient(IntegrationClient):
    PROVIDER = "moneybird"

    def _headers(self) -> dict:
        token = self.credentials.get("access_token")
        if not token:
            raise ValueError("access_token ontbreekt")
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def _admin(self) -> str:
        admin = self.credentials.get("administration_id")
        if not admin:
            raise ValueError("administration_id ontbreekt")
        return str(admin)

    async def _get(self, path: str) -> any:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{BASE}{path}", headers=self._headers())
            if r.status_code == 401:
                raise PermissionError("Ongeldige Moneybird access token")
            r.raise_for_status()
            return r.json()

    async def test_connection(self) -> dict:
        try:
            data = await self._get("/administrations.json")
            admins = data if isinstance(data, list) else []
            target = self._admin()
            match = next((a for a in admins if str(a.get("id")) == target), None)
            if not match:
                return {
                    "status": "error",
                    "message": f"Token werkt maar administration_id {target} niet gevonden ({len(admins)} beschikbaar)",
                }
            return {
                "status": "connected",
                "message": f"Verbonden met Moneybird administration '{match.get('name')}'",
                "metadata": {"administration_name": match.get("name"), "country": match.get("country")},
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        return await self._get(f"/{self._admin()}/contacts.json") or []

    async def list_invoices(self) -> list[dict]:
        return await self._get(f"/{self._admin()}/sales_invoices.json") or []

    async def list_payments(self) -> list[dict]:
        # Moneybird groups payments under financial_mutations
        return await self._get(f"/{self._admin()}/financial_mutations.json") or []
