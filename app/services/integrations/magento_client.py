"""Magento / Adobe Commerce REST API client.

Uses a Bearer integration token for authentication. Tokens are created in
Magento Admin → System → Integrations → Access Token.

Base URL should be the REST V1 endpoint, e.g. https://shop.com/rest/V1

Docs: https://developer.adobe.com/commerce/webapi/rest/
"""
import httpx
from app.services.integrations.base import IntegrationClient


class MagentoClient(IntegrationClient):
    PROVIDER = "magento"

    def _base_url(self) -> str:
        url = self.credentials.get("url", "").rstrip("/")
        if not url:
            raise ValueError("url ontbreekt — vul de Magento REST API base URL in")
        return url

    def _headers(self) -> dict:
        token = self.credentials.get("access_token")
        if not token:
            raise ValueError("access_token ontbreekt")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str) -> any:
        url = f"{self._base_url()}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=self._headers())
            if r.status_code == 401:
                raise PermissionError("Ongeldige Magento access token")
            r.raise_for_status()
            return r.json()

    async def test_connection(self) -> dict:
        try:
            data = await self._get("/store/storeConfigs")
            stores = data if isinstance(data, list) else [data]
            if not stores:
                return {"status": "error", "message": "Geen winkels gevonden via Magento API"}
            first = stores[0] if isinstance(stores[0], dict) else {}
            return {
                "status": "connected",
                "message": f"Verbonden met Magento ({first.get('base_url', 'onbekend')})",
                "metadata": {
                    "store_name": first.get("store_name"),
                    "base_url": first.get("base_url"),
                    "locale": first.get("locale"),
                },
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        data = await self._get("/customers/search?searchCriteria[pageSize]=100")
        if isinstance(data, dict):
            return data.get("items", [])
        return []

    async def list_invoices(self) -> list[dict]:
        data = await self._get("/invoices?searchCriteria[pageSize]=100")
        if isinstance(data, dict):
            return data.get("items", [])
        return []

    async def list_payments(self) -> list[dict]:
        # Magento heeft geen apart payments endpoint — betalingen zitten
        # bij orders/invoices. Retourneer leeg voor nu.
        return []
