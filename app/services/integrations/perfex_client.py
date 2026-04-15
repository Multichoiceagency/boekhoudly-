"""Perfex CRM client (Themesic REST API module).

Wraps the existing PerfexCRMClient in the IntegrationClient interface so it
can be configured per-company via integration_connections instead of env vars.
"""
from app.services.integrations.base import IntegrationClient
from app.services.perfex_service import PerfexCRMClient


class PerfexClient(IntegrationClient):
    PROVIDER = "perfex"

    def _client(self) -> PerfexCRMClient:
        url = self.credentials.get("url")
        api_key = self.credentials.get("api_key")
        if not url or not api_key:
            raise ValueError("url en api_key zijn verplicht voor Perfex")
        return PerfexCRMClient(base_url=url, api_key=api_key)

    async def test_connection(self) -> dict:
        try:
            return await self._client().test_connection()
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    async def list_customers(self) -> list[dict]:
        return await self._client().get_customers()

    async def list_invoices(self) -> list[dict]:
        return await self._client().get_invoices()

    async def list_payments(self) -> list[dict]:
        return await self._client().get_payments()
