"""
Perfex CRM API integration service — Themesic REST API module variant.

This client targets the Themesic Perfex REST API module (perfexcrm.themesic.com)
which uses JWT-based auth via an `authtoken` header. The base URL is the full
API root (e.g. https://crm.example.com/api), without /v1.

Authentication: authtoken header (JWT)
Endpoints (verified against a live install):
  customers, customers/{id}, contacts/{customer_id}, leads, projects, items,
  proposals, estimates, invoices, invoices/{id}, payments, credit_notes,
  contracts, tickets, subscriptions
"""
import logging
from typing import Any
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class PerfexCRMClient:
    """Client for Perfex CRM (Themesic REST API module)."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        raw_base = (base_url or settings.PERFEX_CRM_URL).rstrip('/')
        if not raw_base or not (api_key or settings.PERFEX_CRM_API_KEY):
            raise ValueError("PERFEX_CRM_URL en PERFEX_CRM_API_KEY zijn verplicht")
        # The base may be passed as ".../api" already, or just the CRM host.
        # Normalize so we end on /api.
        self.api_url = raw_base if raw_base.endswith("/api") else f"{raw_base}/api"
        self.api_key = api_key or settings.PERFEX_CRM_API_KEY
        self.headers = {
            "authtoken": self.api_key,
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, params: dict | None = None, json: dict | None = None) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=self.headers, params=params, json=json)
            if response.status_code == 401:
                raise PermissionError("Ongeldige Perfex CRM authtoken")
            if response.status_code == 404:
                # Themesic API returns 404 with {status:false, message:"No data were found"}
                # for empty result sets — treat as empty list.
                try:
                    body = response.json()
                    if isinstance(body, dict) and body.get("status") is False:
                        return []
                except Exception:
                    pass
                return []
            response.raise_for_status()
            return response.json()

    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
        return await self._request("GET", endpoint, params=params)

    async def _post(self, endpoint: str, json: dict | None = None) -> Any:
        return await self._request("POST", endpoint, json=json)

    async def _put(self, endpoint: str, json: dict | None = None) -> Any:
        return await self._request("PUT", endpoint, json=json)

    async def _delete(self, endpoint: str) -> Any:
        return await self._request("DELETE", endpoint)

    @staticmethod
    def _as_list(data: Any) -> list:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Themesic sometimes wraps in {data: [...]}, sometimes returns dict directly
            return data.get("data") or [data]
        return []

    # ---- Test Connection ----
    async def test_connection(self) -> dict:
        try:
            data = await self._get("customers")
            count = len(self._as_list(data))
            return {"status": "connected", "message": f"Verbonden met Perfex CRM ({count} klanten)", "customer_count": count}
        except PermissionError:
            return {"status": "error", "message": "Ongeldige authtoken"}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    # ---- Customers ----
    async def get_customers(self) -> list[dict]:
        return self._as_list(await self._get("customers"))

    async def get_customer(self, customer_id: str | int) -> dict:
        data = await self._get(f"customers/{customer_id}")
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else {}

    async def create_customer(self, customer: dict) -> dict:
        return await self._post("customers", json=customer)

    # ---- Contacts (per customer) ----
    async def get_customer_contacts(self, customer_id: str | int) -> list[dict]:
        return self._as_list(await self._get(f"contacts/{customer_id}"))

    # ---- Invoices ----
    async def get_invoices(self) -> list[dict]:
        return self._as_list(await self._get("invoices"))

    async def get_invoice(self, invoice_id: str | int) -> dict:
        data = await self._get(f"invoices/{invoice_id}")
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else {}

    async def create_invoice(self, invoice: dict) -> dict:
        return await self._post("invoices", json=invoice)

    # ---- Payments ----
    async def get_payments(self) -> list[dict]:
        return self._as_list(await self._get("payments"))

    # ---- Estimates ----
    async def get_estimates(self) -> list[dict]:
        return self._as_list(await self._get("estimates"))

    # ---- Proposals ----
    async def get_proposals(self) -> list[dict]:
        return self._as_list(await self._get("proposals"))

    # ---- Credit notes ----
    async def get_credit_notes(self) -> list[dict]:
        return self._as_list(await self._get("credit_notes"))

    # ---- Subscriptions ----
    async def get_subscriptions(self) -> list[dict]:
        return self._as_list(await self._get("subscriptions"))

    # ---- Leads ----
    async def get_leads(self) -> list[dict]:
        return self._as_list(await self._get("leads"))

    # ---- Projects ----
    async def get_projects(self) -> list[dict]:
        return self._as_list(await self._get("projects"))

    # ---- Items (catalog) ----
    async def get_items(self) -> list[dict]:
        return self._as_list(await self._get("items"))

    # ---- Tickets ----
    async def get_tickets(self) -> list[dict]:
        return self._as_list(await self._get("tickets"))

    # ---- Contracts ----
    async def get_contracts(self) -> list[dict]:
        return self._as_list(await self._get("contracts"))

    # ---- Full Sync ----
    async def sync_all(self) -> dict:
        """Fetch all key resources from Perfex for an import overview."""
        result: dict = {}
        resources = {
            "customers": self.get_customers,
            "invoices": self.get_invoices,
            "payments": self.get_payments,
            "estimates": self.get_estimates,
            "proposals": self.get_proposals,
            "credit_notes": self.get_credit_notes,
            "subscriptions": self.get_subscriptions,
            "leads": self.get_leads,
            "projects": self.get_projects,
            "items": self.get_items,
            "tickets": self.get_tickets,
            "contracts": self.get_contracts,
        }
        for name, fetcher in resources.items():
            try:
                items = await fetcher()
                result[name] = items
                logger.info(f"Perfex sync: {len(items)} {name}")
            except Exception as e:
                logger.warning(f"Perfex sync failed for {name}: {e}")
                result[name] = []
        return result
