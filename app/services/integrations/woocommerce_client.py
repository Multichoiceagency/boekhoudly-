"""WooCommerce REST API v3 client.

Auth via HTTP Basic (consumer_key / consumer_secret).
Base URL: {shop_url}/wp-json/wc/v3

Docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
"""
import httpx
from app.services.integrations.base import IntegrationClient


class WooCommerceClient(IntegrationClient):
    PROVIDER = "woocommerce"

    def _base_url(self) -> str:
        url = self.credentials.get("url", "").rstrip("/")
        if not url:
            raise ValueError("Shop URL ontbreekt")
        return f"{url}/wp-json/wc/v3"

    def _auth(self) -> tuple[str, str]:
        key = self.credentials.get("consumer_key")
        secret = self.credentials.get("consumer_secret")
        if not key or not secret:
            raise ValueError("consumer_key en consumer_secret zijn verplicht")
        return (key, secret)

    async def _get(self, path: str, params: dict | None = None) -> any:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{self._base_url()}{path}",
                auth=self._auth(),
                params=params or {},
            )
            if r.status_code == 401:
                raise PermissionError("Ongeldige WooCommerce API-sleutels")
            r.raise_for_status()
            return r.json()

    # ------------------------------------------------------------------
    # test_connection
    # ------------------------------------------------------------------
    async def test_connection(self) -> dict:
        try:
            data = await self._get("/system_status")
            env = data.get("environment", {})
            store = data.get("settings", {})
            return {
                "status": "connected",
                "message": (
                    f"Verbonden met WooCommerce op "
                    f"{self.credentials.get('url', '?')}"
                ),
                "metadata": {
                    "wc_version": env.get("version", "onbekend"),
                    "wp_version": env.get("wp_version", "onbekend"),
                    "store_currency": store.get("currency", "onbekend"),
                },
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "message": f"WooCommerce API fout (HTTP {e.response.status_code}): "
                           f"{str(e)[:200]}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    # ------------------------------------------------------------------
    # list_customers
    # ------------------------------------------------------------------
    async def list_customers(self) -> list[dict]:
        raw = await self._get("/customers", {"per_page": 100})
        return [
            {
                "id": c.get("id"),
                "name": " ".join(
                    filter(None, [
                        c.get("billing", {}).get("first_name"),
                        c.get("billing", {}).get("last_name"),
                    ])
                ),
                "email": c.get("email"),
            }
            for c in (raw or [])
        ]

    # ------------------------------------------------------------------
    # list_invoices  (WooCommerce uses "orders" as invoices)
    # ------------------------------------------------------------------
    async def list_invoices(self) -> list[dict]:
        raw = await self._get("/orders", {"per_page": 100})
        return [
            {
                "id": o.get("id"),
                "name": o.get("number"),
                "email": o.get("billing", {}).get("email"),
                "total": o.get("total"),
                "status": o.get("status"),
                "date": o.get("date_created"),
            }
            for o in (raw or [])
        ]

    # ------------------------------------------------------------------
    # list_payments  (payments are embedded inside orders)
    # ------------------------------------------------------------------
    async def list_payments(self) -> list[dict]:
        return []
