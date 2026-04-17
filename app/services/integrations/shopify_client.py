"""Shopify Admin REST API 2024-01 client.

Auth via X-Shopify-Access-Token header (custom app / private app token).
Base URL: https://{shop_url}/admin/api/2024-01

Docs: https://shopify.dev/docs/api/admin-rest
"""
import httpx
from app.services.integrations.base import IntegrationClient

API_VERSION = "2024-01"


class ShopifyClient(IntegrationClient):
    PROVIDER = "shopify"

    def _base_url(self) -> str:
        shop = self.credentials.get("shop_url", "").rstrip("/")
        if not shop:
            raise ValueError("Shop URL ontbreekt")
        # Ensure the URL has a scheme
        if not shop.startswith("http"):
            shop = f"https://{shop}"
        return f"{shop}/admin/api/{API_VERSION}"

    def _headers(self) -> dict:
        token = self.credentials.get("access_token")
        if not token:
            raise ValueError("access_token ontbreekt")
        return {
            "X-Shopify-Access-Token": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict | None = None) -> any:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{self._base_url()}{path}",
                headers=self._headers(),
                params=params or {},
            )
            if r.status_code == 401:
                raise PermissionError("Ongeldig Shopify access token")
            if r.status_code == 403:
                raise PermissionError(
                    "Shopify access token heeft onvoldoende rechten"
                )
            r.raise_for_status()
            return r.json()

    # ------------------------------------------------------------------
    # test_connection
    # ------------------------------------------------------------------
    async def test_connection(self) -> dict:
        try:
            data = await self._get("/shop.json")
            shop = data.get("shop", {})
            return {
                "status": "connected",
                "message": (
                    f"Verbonden met Shopify winkel '{shop.get('name', '?')}'"
                ),
                "metadata": {
                    "shop_name": shop.get("name"),
                    "domain": shop.get("domain"),
                    "currency": shop.get("currency"),
                    "plan": shop.get("plan_display_name"),
                },
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "message": f"Shopify API fout (HTTP {e.response.status_code}): "
                           f"{str(e)[:200]}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    # ------------------------------------------------------------------
    # list_customers
    # ------------------------------------------------------------------
    async def list_customers(self) -> list[dict]:
        data = await self._get("/customers.json", {"limit": 250})
        raw = data.get("customers", [])
        return [
            {
                "id": c.get("id"),
                "name": " ".join(
                    filter(None, [
                        c.get("first_name"),
                        c.get("last_name"),
                    ])
                ),
                "email": c.get("email"),
            }
            for c in raw
        ]

    # ------------------------------------------------------------------
    # list_invoices  (Shopify uses "orders" as invoices)
    # ------------------------------------------------------------------
    async def list_invoices(self) -> list[dict]:
        data = await self._get("/orders.json", {"limit": 250, "status": "any"})
        raw = data.get("orders", [])
        return [
            {
                "id": o.get("id"),
                "number": o.get("order_number"),
                "total_price": o.get("total_price"),
                "financial_status": o.get("financial_status"),
                "created_at": o.get("created_at"),
            }
            for o in raw
        ]

    # ------------------------------------------------------------------
    # list_payments  (payments are embedded inside orders)
    # ------------------------------------------------------------------
    async def list_payments(self) -> list[dict]:
        return []
