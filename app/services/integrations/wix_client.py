"""Wix eCommerce API client.

Uses an API key + site ID for authentication. API keys are created in
Wix → Developer Center → API Keys.

Docs: https://dev.wix.com/docs/rest
"""
import httpx
from app.services.integrations.base import IntegrationClient

BASE = "https://www.wixapis.com/stores/v2"


class WixClient(IntegrationClient):
    PROVIDER = "wix"

    def _api_key(self) -> str:
        key = self.credentials.get("api_key")
        if not key:
            raise ValueError("api_key ontbreekt")
        return key

    def _site_id(self) -> str:
        site_id = self.credentials.get("site_id")
        if not site_id:
            raise ValueError("site_id ontbreekt")
        return site_id

    def _headers(self) -> dict:
        return {
            "Authorization": self._api_key(),
            "wix-site-id": self._site_id(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _post(self, path: str, body: dict | None = None) -> any:
        url = f"{BASE}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=self._headers(), json=body or {})
            if r.status_code == 401:
                raise PermissionError("Ongeldige Wix API key of site ID")
            r.raise_for_status()
            return r.json()

    async def _get(self, path: str) -> any:
        url = f"{BASE}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=self._headers())
            if r.status_code == 401:
                raise PermissionError("Ongeldige Wix API key of site ID")
            r.raise_for_status()
            return r.json()

    async def test_connection(self) -> dict:
        try:
            # Wix uses POST for query endpoints — a successful products query
            # confirms the API key and site ID are valid.
            data = await self._post("/products/query", {"query": {"paging": {"limit": 1}}})
            total = 0
            if isinstance(data, dict):
                total = data.get("totalResults", len(data.get("products", [])))
            return {
                "status": "connected",
                "message": f"Verbonden met Wix eCommerce ({total} producten gevonden)",
                "metadata": {"total_products": total},
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        raise NotImplementedError("Wix klanten-sync wordt binnenkort ondersteund")

    async def list_invoices(self) -> list[dict]:
        # Wix uses POST for order queries
        data = await self._post("/orders/query", {"query": {"paging": {"limit": 100}}})
        if isinstance(data, dict):
            return data.get("orders", [])
        return []

    async def list_payments(self) -> list[dict]:
        # Wix betalingen zitten bij de orders — retourneer leeg voor nu.
        return []
