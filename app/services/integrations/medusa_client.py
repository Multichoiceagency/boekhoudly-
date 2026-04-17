"""Medusa Admin API client.

Supports both header-based auth styles:
  - x-medusa-access-token: {api_key}
  - Authorization: Bearer {api_key}

Base URL is the Medusa backend root (e.g. https://api.shop.com). The /admin
prefix is appended automatically.

Docs: https://docs.medusajs.com/api/admin
"""
import httpx
from app.services.integrations.base import IntegrationClient


class MedusaClient(IntegrationClient):
    PROVIDER = "medusa"

    def _base_url(self) -> str:
        url = self.credentials.get("url", "").rstrip("/")
        if not url:
            raise ValueError("url ontbreekt — vul de Medusa backend URL in")
        return f"{url}/admin"

    def _api_key(self) -> str:
        key = self.credentials.get("api_key")
        if not key:
            raise ValueError("api_key ontbreekt")
        return key

    def _headers(self) -> dict:
        key = self._api_key()
        return {
            "Authorization": f"Bearer {key}",
            "x-medusa-access-token": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict | None = None) -> any:
        url = f"{self._base_url()}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=self._headers(), params=params)
            if r.status_code == 401:
                raise PermissionError("Ongeldige Medusa API key")
            r.raise_for_status()
            return r.json()

    async def test_connection(self) -> dict:
        try:
            data = await self._get("/store")
            store = data if isinstance(data, dict) else {}
            # Medusa wraps the response in a "store" key
            info = store.get("store", store)
            return {
                "status": "connected",
                "message": f"Verbonden met Medusa ({info.get('name', 'onbekend')})",
                "metadata": {
                    "store_name": info.get("name"),
                    "currencies": info.get("currencies"),
                    "default_currency": info.get("default_currency_code"),
                },
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        data = await self._get("/customers", params={"limit": 100})
        if isinstance(data, dict):
            return data.get("customers", [])
        return []

    async def list_invoices(self) -> list[dict]:
        # Medusa has no dedicated invoices — orders are used instead
        data = await self._get("/orders", params={"limit": 100})
        if isinstance(data, dict):
            return data.get("orders", [])
        return []

    async def list_payments(self) -> list[dict]:
        data = await self._get("/payments", params={"limit": 100})
        if isinstance(data, dict):
            return data.get("payments", [])
        return []
