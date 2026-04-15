"""Multi-provider CRM/accounting integration framework.

Each provider is a subclass of `IntegrationClient` that takes a credentials
dict (loaded from the `integration_connections` table) and exposes a uniform
interface for testing the connection and listing customers/invoices/payments.
"""
from app.services.integrations.base import IntegrationClient, ProviderSpec, PROVIDERS
from app.services.integrations.perfex_client import PerfexClient
from app.services.integrations.moneybird_client import MoneybirdClient
from app.services.integrations.wefact_client import WeFactClient
from app.services.integrations.twinfield_client import TwinfieldClient
from app.services.integrations.yuki_client import YukiClient


_REGISTRY = {
    "perfex": PerfexClient,
    "moneybird": MoneybirdClient,
    "wefact": WeFactClient,
    "twinfield": TwinfieldClient,
    "yuki": YukiClient,
}


def get_client(provider: str, credentials: dict) -> IntegrationClient:
    cls = _REGISTRY.get(provider)
    if not cls:
        raise ValueError(f"Onbekende integratie provider: {provider}")
    return cls(credentials)


__all__ = ["IntegrationClient", "ProviderSpec", "PROVIDERS", "get_client"]
