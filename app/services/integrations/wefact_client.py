"""WeFact API v2 client.

WeFact uses a flat POST endpoint where you specify controller + action +
api_key as form fields. Auth is purely the api_key.

Docs: https://www.wefact.nl/api/
"""
import httpx
from app.services.integrations.base import IntegrationClient

BASE = "https://api.mijnwefact.nl/v2/"


class WeFactClient(IntegrationClient):
    PROVIDER = "wefact"

    def _api_key(self) -> str:
        key = self.credentials.get("api_key")
        if not key:
            raise ValueError("api_key ontbreekt")
        return key

    async def _call(self, controller: str, action: str, params: dict | None = None) -> dict:
        body = {
            "api_key": self._api_key(),
            "controller": controller,
            "action": action,
            **(params or {}),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(BASE, data=body)
            r.raise_for_status()
            return r.json()

    async def test_connection(self) -> dict:
        try:
            data = await self._call("accountmanager", "show")
            if data.get("status") == "success":
                am = data.get("accountmanager", {}) or {}
                return {
                    "status": "connected",
                    "message": f"Verbonden met WeFact ({am.get('CompanyName', 'onbekend')})",
                    "metadata": {"company_name": am.get("CompanyName"), "email": am.get("EmailAddress")},
                }
            return {"status": "error", "message": data.get("errors", ["Onbekende fout"])[0] if data.get("errors") else "Niet verbonden"}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        data = await self._call("debtor", "list")
        return data.get("debtors", []) if data.get("status") == "success" else []

    async def list_invoices(self) -> list[dict]:
        data = await self._call("invoice", "list")
        return data.get("invoices", []) if data.get("status") == "success" else []

    async def list_payments(self) -> list[dict]:
        # WeFact tracks payments inside invoice records — return empty for now
        # and aggregate via list_invoices on the consumer side.
        return []
