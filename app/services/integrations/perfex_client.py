"""Perfex CRM client (Themesic REST API module).

Wraps the existing PerfexCRMClient in the IntegrationClient interface so it
can be configured per-company via integration_connections instead of env vars.
"""
import asyncio
import logging

from app.services.integrations.base import IntegrationClient
from app.services.perfex_service import PerfexCRMClient

logger = logging.getLogger(__name__)


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
        """Return customers, hydrating each with full details (address, phone,
        zip) that the list endpoint omits on some Perfex installs."""
        client = self._client()
        summary = await client.get_customers()

        async def _hydrate(c: dict) -> dict:
            uid = c.get("userid") or c.get("id")
            if not uid:
                return c
            try:
                detail = await client.get_customer(uid)
            except Exception as e:
                logger.debug(f"Perfex customer {uid} detail fetch failed: {e}")
                return c
            # Merge detail over summary so richer fields win.
            return {**c, **(detail or {})}

        # Bound concurrency: Perfex installs rate-limit aggressively.
        sem = asyncio.Semaphore(5)

        async def _bound(c):
            async with sem:
                return await _hydrate(c)

        return await asyncio.gather(*[_bound(c) for c in summary])

    async def list_invoices(self) -> list[dict]:
        """Return invoices with the `items` array populated. The bulk
        /invoices endpoint returns summaries without line items — each
        invoice must be fetched individually to get its items."""
        client = self._client()
        summary = await client.get_invoices()

        async def _hydrate(inv: dict) -> dict:
            iid = inv.get("id")
            if not iid:
                return inv
            try:
                detail = await client.get_invoice(iid)
            except Exception as e:
                logger.debug(f"Perfex invoice {iid} detail fetch failed: {e}")
                return inv
            return {**inv, **(detail or {})}

        sem = asyncio.Semaphore(5)

        async def _bound(inv):
            async with sem:
                return await _hydrate(inv)

        return await asyncio.gather(*[_bound(i) for i in summary])

    async def list_payments(self) -> list[dict]:
        return await self._client().get_payments()
