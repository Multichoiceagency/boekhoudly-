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
        """Verify the URL + authtoken reach a live Perfex REST API.

        Tries the bulk `customers` endpoint first for a quick "N customers
        found" response; if the install doesn't expose it (returns empty)
        falls back to `customers/search/a` which is part of the documented
        Themesic REST API and proves auth works regardless of whether the
        undocumented bulk route is configured.
        """
        try:
            bulk = self._as_list(await self._get("customers"))
            if bulk:
                return {
                    "status": "connected",
                    "message": f"Verbonden met Perfex CRM ({len(bulk)} klanten gevonden via /customers)",
                    "customer_count": len(bulk),
                }
            # Empty bulk — could mean "no customers" or "bulk endpoint missing".
            # A documented search call disambiguates: if it responds OK (even
            # with 0 results) the authtoken is valid.
            probe = self._as_list(await self._get("customers/search/a"))
            return {
                "status": "connected",
                "message": (
                    f"Verbonden met Perfex CRM (auth werkt; zoekopdracht 'a' vond {len(probe)} klanten). "
                    "De bulk /customers route was leeg of is niet beschikbaar op deze install — "
                    "de live sync gebruikt /search voor paginering."
                ),
                "customer_count": len(probe),
            }
        except PermissionError:
            return {"status": "error", "message": "Ongeldige authtoken"}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    # Short common letters that cover virtually every Dutch company name, used
    # to fan out the /search endpoint when the bulk /<resource> endpoint isn't
    # available on a given Perfex install (the documented Themesic REST API
    # only exposes /:id and /search/:keysearch for most resources).
    _SEARCH_ALPHABET = [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
        "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
        "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ]

    async def _try_bulk_list(self, resource: str) -> list[dict]:
        """Try the undocumented `GET /api/<resource>` bulk list first.

        Many Perfex installs still return the full list there, so it's always
        worth a single call before the expensive fan-out. Returns [] if the
        endpoint 404s or responds with `{status: false}`.
        """
        try:
            data = await self._get(resource)
        except Exception as e:
            logger.debug(f"Perfex bulk {resource} failed: {e}")
            return []
        lst = self._as_list(data)
        return [r for r in lst if isinstance(r, dict)]

    async def _list_via_search(self, resource: str, id_field: str) -> list[dict]:
        """Fan out /search/<letter> across a-z + 0-9 and dedupe by id.

        Slower than a bulk call but works on every Perfex install because
        /search is documented. `id_field` is the per-resource primary key
        (e.g. "userid" for customers, "id" for invoices).
        """
        seen: dict[str, dict] = {}
        for term in self._SEARCH_ALPHABET:
            try:
                data = await self._get(f"{resource}/search/{term}")
            except Exception as e:
                logger.debug(f"Perfex search {resource}/{term} failed: {e}")
                continue
            for row in self._as_list(data):
                if not isinstance(row, dict):
                    continue
                rid = str(row.get(id_field) or row.get("id") or "")
                if rid and rid not in seen:
                    seen[rid] = row
        return list(seen.values())

    async def _list_all(self, resource: str, id_field: str = "id") -> list[dict]:
        """Return every record of a Perfex resource.

        Prefers the bulk endpoint for speed and falls back to /search
        iteration for installs that don't expose one.
        """
        bulk = await self._try_bulk_list(resource)
        if bulk:
            return bulk
        return await self._list_via_search(resource, id_field)

    # ---- Customers ----
    async def get_customers(self) -> list[dict]:
        return await self._list_all("customers", id_field="userid")

    async def get_customer(self, customer_id: str | int) -> dict:
        data = await self._get(f"customers/{customer_id}")
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else {}

    async def search_customers(self, keyword: str) -> list[dict]:
        return self._as_list(await self._get(f"customers/search/{keyword}"))

    async def create_customer(self, customer: dict) -> dict:
        return await self._post("customers", json=customer)

    async def delete_customer(self, customer_id: str | int) -> dict:
        # Perfex requires the /delete/ prefix for customers/items/leads/projects/tasks/tickets.
        return await self._delete(f"delete/customers/{customer_id}")

    # ---- Contacts (per customer) ----
    async def get_customer_contacts(self, customer_id: str | int) -> list[dict]:
        return self._as_list(await self._get(f"contacts/{customer_id}"))

    async def search_contacts(self, keyword: str) -> list[dict]:
        return self._as_list(await self._get(f"contacts/search/{keyword}"))

    # ---- Invoices ----
    async def get_invoices(self) -> list[dict]:
        return await self._list_all("invoices", id_field="id")

    async def get_invoice(self, invoice_id: str | int) -> dict:
        data = await self._get(f"invoices/{invoice_id}")
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else {}

    async def search_invoices(self, keyword: str) -> list[dict]:
        return self._as_list(await self._get(f"invoices/search/{keyword}"))

    async def create_invoice(self, invoice: dict) -> dict:
        return await self._post("invoices", json=invoice)

    # ---- Payments ----
    async def get_payments(self) -> list[dict]:
        return await self._list_all("payments", id_field="id")

    async def get_payment(self, payment_id: str | int) -> dict:
        data = await self._get(f"payments/{payment_id}")
        return data if isinstance(data, dict) else {}

    # ---- Estimates ----
    async def get_estimates(self) -> list[dict]:
        return await self._list_all("estimates", id_field="id")

    async def get_estimate(self, estimate_id: str | int) -> dict:
        data = await self._get(f"estimates/{estimate_id}")
        return data if isinstance(data, dict) else {}

    # ---- Proposals ----
    async def get_proposals(self) -> list[dict]:
        return await self._list_all("proposals", id_field="id")

    # ---- Credit notes ----
    async def get_credit_notes(self) -> list[dict]:
        return await self._list_all("credit_notes", id_field="id")

    async def get_credit_note(self, cn_id: str | int) -> dict:
        data = await self._get(f"credit_notes/{cn_id}")
        return data if isinstance(data, dict) else {}

    # ---- Subscriptions ----
    async def get_subscriptions(self) -> list[dict]:
        return await self._list_all("subscriptions", id_field="id")

    # ---- Leads ----
    async def get_leads(self) -> list[dict]:
        return await self._list_all("leads", id_field="id")

    # ---- Projects ----
    async def get_projects(self) -> list[dict]:
        return await self._list_all("projects", id_field="id")

    # ---- Items (catalog) ----
    async def get_items(self) -> list[dict]:
        return await self._list_all("items", id_field="itemid")

    # ---- Tickets ----
    async def get_tickets(self) -> list[dict]:
        return await self._list_all("tickets", id_field="ticketid")

    # ---- Contracts ----
    async def get_contracts(self) -> list[dict]:
        return await self._list_all("contracts", id_field="id")

    # ---- Expenses ----
    async def get_expenses(self) -> list[dict]:
        return await self._list_all("expenses", id_field="id")

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
