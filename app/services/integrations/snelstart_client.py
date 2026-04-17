"""SnelStart B2B API v2 client.

Authenticatie via Basic Auth (client_key als wachtwoord) en de
Ocp-Apim-Subscription-Key header.

Docs: https://b2bapi-developer.snelstart.nl/
"""
import httpx
from base64 import b64encode

from app.services.integrations.base import IntegrationClient

BASE_URL = "https://b2bapi.snelstart.nl/v2"


class SnelStartClient(IntegrationClient):
    PROVIDER = "snelstart"

    def _headers(self) -> dict:
        client_key = self.credentials.get("client_key")
        subscription_key = self.credentials.get("subscription_key")
        if not client_key:
            raise ValueError("client_key ontbreekt")
        if not subscription_key:
            raise ValueError("subscription_key ontbreekt")

        # SnelStart B2B uses Basic auth with empty username and client_key as password
        basic = b64encode(f":{client_key}".encode()).decode()
        return {
            "Authorization": f"Basic {basic}",
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Accept": "application/json",
        }

    async def _get(self, path: str) -> any:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{BASE_URL}{path}", headers=self._headers())
            if r.status_code == 401:
                raise PermissionError("Ongeldige SnelStart client_key of subscription_key")
            if r.status_code == 403:
                raise PermissionError("Geen toegang — controleer je SnelStart subscription")
            r.raise_for_status()
            return r.json()

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------
    async def test_connection(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(
                    f"{BASE_URL}/echo",
                    headers=self._headers(),
                )
            if r.status_code == 200:
                return {
                    "status": "connected",
                    "message": "Verbonden met SnelStart B2B API",
                }
            return {
                "status": "error",
                "message": f"SnelStart echo endpoint HTTP {r.status_code}: {r.text[:200]}",
            }
        except PermissionError as e:
            return {"status": "error", "message": str(e)}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:200]}"}

    # ------------------------------------------------------------------
    # Customers (relaties)
    # ------------------------------------------------------------------
    async def list_customers(self) -> list[dict]:
        try:
            raw = await self._get("/relaties") or []
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("naam", ""),
                    "email": r.get("email", ""),
                    "phone": r.get("telefoon", ""),
                    "address": r.get("adres", {}).get("straat", "") if isinstance(r.get("adres"), dict) else "",
                    "city": r.get("adres", {}).get("plaats", "") if isinstance(r.get("adres"), dict) else "",
                    "postal_code": r.get("adres", {}).get("postcode", "") if isinstance(r.get("adres"), dict) else "",
                    "country": r.get("adres", {}).get("land", "") if isinstance(r.get("adres"), dict) else "",
                    "vat_number": r.get("btwNummer", ""),
                    "type": r.get("relatiesoort", []),
                    "raw": r,
                }
                for r in raw
            ]
        except PermissionError as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Fout bij ophalen klanten: {str(e)[:200]}") from e

    # ------------------------------------------------------------------
    # Invoices (verkoopfacturen)
    # ------------------------------------------------------------------
    async def list_invoices(self) -> list[dict]:
        try:
            raw = await self._get("/verkoopfacturen") or []
            return [
                {
                    "id": inv.get("id"),
                    "invoice_number": inv.get("factuurnummer", ""),
                    "date": inv.get("factuurdatum", ""),
                    "due_date": inv.get("vervalDatum", ""),
                    "amount": inv.get("factuurbedrag", 0),
                    "amount_open": inv.get("openstaandSaldo", 0),
                    "currency": "EUR",
                    "customer_id": inv.get("relatie", {}).get("id") if isinstance(inv.get("relatie"), dict) else None,
                    "customer_name": inv.get("relatie", {}).get("naam", "") if isinstance(inv.get("relatie"), dict) else "",
                    "status": "paid" if inv.get("openstaandSaldo", 1) == 0 else "open",
                    "raw": inv,
                }
                for inv in raw
            ]
        except PermissionError as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Fout bij ophalen facturen: {str(e)[:200]}") from e

    # ------------------------------------------------------------------
    # Payments (bankboekingen)
    # ------------------------------------------------------------------
    async def list_payments(self) -> list[dict]:
        try:
            raw = await self._get("/bankboekingen") or []
            return [
                {
                    "id": p.get("id"),
                    "date": p.get("datum", ""),
                    "description": p.get("omschrijving", ""),
                    "amount": p.get("bedrag", 0),
                    "currency": "EUR",
                    "raw": p,
                }
                for p in raw
            ]
        except PermissionError as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Fout bij ophalen betalingen: {str(e)[:200]}") from e
