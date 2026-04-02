"""
GoCardless (Nordigen) Bank Integration Service
Provides PSD2-compliant bank account linking and transaction fetching
for Dutch and European banks.
"""
import httpx
from datetime import datetime, timedelta
from app.config import get_settings

settings = get_settings()


class GoCardlessService:
    """Service for GoCardless Bank Account Data API (formerly Nordigen)."""

    def __init__(self):
        self.base_url = settings.GOCARDLESS_BASE_URL
        self.secret_id = settings.GOCARDLESS_SECRET_ID
        self.secret_key = settings.GOCARDLESS_SECRET_KEY
        self._access_token = None
        self._token_expires = None

    async def _get_token(self) -> str:
        """Get or refresh the GoCardless access token."""
        if self._access_token and self._token_expires and datetime.utcnow() < self._token_expires:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/token/new/",
                json={
                    "secret_id": self.secret_id,
                    "secret_key": self.secret_key,
                },
            )

        if response.status_code != 200:
            raise Exception(f"GoCardless auth failed: {response.text}")

        data = response.json()
        self._access_token = data["access"]
        # Token expires in 24h, refresh at 23h
        self._token_expires = datetime.utcnow() + timedelta(hours=23)
        return self._access_token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_institutions(self, country: str = "NL") -> list[dict]:
        """Get available banks/institutions for a country."""
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/institutions/?country={country}",
                headers=headers,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get institutions: {response.text}")

        return response.json()

    async def create_requisition(
        self, institution_id: str, redirect_url: str, reference: str
    ) -> dict:
        """Create a bank connection requisition (link session)."""
        headers = await self._headers()

        # First create an end-user agreement
        async with httpx.AsyncClient() as client:
            agreement_response = await client.post(
                f"{self.base_url}/agreements/enduser/",
                headers=headers,
                json={
                    "institution_id": institution_id,
                    "max_historical_days": 730,  # 2 years
                    "access_valid_for_days": 180,
                    "access_scope": ["balances", "details", "transactions"],
                },
            )

        if agreement_response.status_code not in (200, 201):
            raise Exception(f"Failed to create agreement: {agreement_response.text}")

        agreement = agreement_response.json()

        # Create requisition with the agreement
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/requisitions/",
                headers=headers,
                json={
                    "redirect": redirect_url,
                    "institution_id": institution_id,
                    "reference": reference,
                    "agreement": agreement["id"],
                    "user_language": "NL",
                },
            )

        if response.status_code not in (200, 201):
            raise Exception(f"Failed to create requisition: {response.text}")

        return response.json()

    async def get_requisition(self, requisition_id: str) -> dict:
        """Get requisition status and linked accounts."""
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/requisitions/{requisition_id}/",
                headers=headers,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get requisition: {response.text}")

        return response.json()

    async def get_account_details(self, account_id: str) -> dict:
        """Get bank account details (IBAN, owner, etc.)."""
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/details/",
                headers=headers,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get account details: {response.text}")

        return response.json()

    async def get_account_balances(self, account_id: str) -> dict:
        """Get current account balances."""
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/balances/",
                headers=headers,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get balances: {response.text}")

        return response.json()

    async def get_transactions(
        self, account_id: str, date_from: str | None = None, date_to: str | None = None
    ) -> dict:
        """Get account transactions within a date range."""
        headers = await self._headers()
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{account_id}/transactions/",
                headers=headers,
                params=params,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to get transactions: {response.text}")

        return response.json()

    async def delete_requisition(self, requisition_id: str) -> bool:
        """Delete/revoke a bank connection."""
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/requisitions/{requisition_id}/",
                headers=headers,
            )
        return response.status_code in (200, 204)


# Singleton instance
bank_service = GoCardlessService()
