"""
Perfex CRM API integration service.

Authentication: X-API-KEY header
Base URL: {PERFEX_CRM_URL}/api/v1
Endpoints: customers, invoices, payments, expenses, contacts, leads, projects, staff
"""
import logging
from typing import Any
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class PerfexCRMClient:
    """Client for Perfex CRM REST API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.PERFEX_CRM_URL).rstrip('/')
        self.api_key = api_key or settings.PERFEX_CRM_API_KEY
        if not self.base_url or not self.api_key:
            raise ValueError("Perfex CRM URL and API key are required")
        self.api_url = f"{self.base_url}/api/v1"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, params: dict | None = None, json: dict | None = None) -> dict:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=self.headers, params=params, json=json)
            if response.status_code == 401:
                raise PermissionError("Ongeldige Perfex CRM API key")
            response.raise_for_status()
            return response.json()

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        return await self._request("GET", endpoint, params=params)

    async def _post(self, endpoint: str, json: dict | None = None) -> dict:
        return await self._request("POST", endpoint, json=json)

    async def _put(self, endpoint: str, json: dict | None = None) -> dict:
        return await self._request("PUT", endpoint, json=json)

    async def _delete(self, endpoint: str) -> dict:
        return await self._request("DELETE", endpoint)

    # ---- Test Connection ----
    async def test_connection(self) -> dict:
        """Test if the API key and URL are valid."""
        try:
            data = await self._get("customers", params={"per_page": 1})
            return {"status": "connected", "message": "Verbinding met Perfex CRM geslaagd"}
        except PermissionError:
            return {"status": "error", "message": "Ongeldige API key"}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)}"}

    # ---- Customers ----
    async def get_customers(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("customers", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    async def get_customer(self, customer_id: int) -> dict:
        return await self._get(f"customers/{customer_id}")

    async def create_customer(self, customer: dict) -> dict:
        return await self._post("customers", json=customer)

    # ---- Contacts ----
    async def get_contacts(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("contacts", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Invoices ----
    async def get_invoices(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("invoices", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    async def get_invoice(self, invoice_id: int) -> dict:
        return await self._get(f"invoices/{invoice_id}")

    async def create_invoice(self, invoice: dict) -> dict:
        return await self._post("invoices", json=invoice)

    # ---- Payments ----
    async def get_payments(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("payments", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Expenses ----
    async def get_expenses(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("expenses", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Leads ----
    async def get_leads(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("leads", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Projects ----
    async def get_projects(self, page: int = 1, per_page: int = 100) -> list[dict]:
        data = await self._get("projects", params={"page": page, "per_page": per_page})
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Staff ----
    async def get_staff(self) -> list[dict]:
        data = await self._get("staff")
        return data.get("data", data) if isinstance(data, dict) else data

    # ---- Full Sync: Get All Data ----
    async def sync_all(self) -> dict:
        """Fetch all data from Perfex CRM for initial import."""
        result = {}
        for resource in ["customers", "invoices", "payments", "expenses", "contacts", "leads", "projects"]:
            try:
                all_items = []
                page = 1
                while True:
                    data = await self._get(resource, params={"page": page, "per_page": 100})
                    items = data.get("data", data) if isinstance(data, dict) else data
                    if not items or not isinstance(items, list):
                        break
                    all_items.extend(items)
                    if len(items) < 100:
                        break
                    page += 1
                result[resource] = all_items
                logger.info(f"Perfex sync: {len(all_items)} {resource}")
            except Exception as e:
                logger.warning(f"Perfex sync failed for {resource}: {e}")
                result[resource] = []
        return result
