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
        url = (self.credentials.get("url") or "").strip()
        api_key = (self.credentials.get("api_key") or "").strip()
        missing = []
        if not url: missing.append("API URL")
        if not api_key: missing.append("JWT authtoken")
        if missing:
            raise ValueError(
                f"{' + '.join(missing)} ontbreekt op de opgeslagen koppeling. "
                "Open Integraties → Perfex → Bewerken en vul het in."
            )
        return PerfexCRMClient(base_url=url, api_key=api_key)

    async def test_connection(self) -> dict:
        try:
            return await self._client().test_connection()
        except ValueError as e:
            return {"status": "error", "message": str(e) or "Ongeldige koppelingsdata"}
        except Exception as e:
            detail = str(e) or type(e).__name__
            return {"status": "error", "message": f"Verbinding mislukt: {detail[:400]}"}

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
