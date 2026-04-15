from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CredentialField:
    key: str
    label: str
    type: str = "text"  # text, password, url, select
    placeholder: str = ""
    required: bool = True
    help: str | None = None
    options: list | None = None


@dataclass
class ProviderSpec:
    slug: str
    name: str
    tagline: str
    icon: str
    color: str
    docs_url: str
    fields: list[CredentialField]
    status: str = "stable"  # stable, beta, coming_soon


PROVIDERS: list[ProviderSpec] = [
    ProviderSpec(
        slug="perfex", name="Perfex CRM", tagline="Klanten, facturen, betalingen uit Perfex",
        icon="📒", color="bg-blue-500", docs_url="https://perfexcrm.themesic.com",
        fields=[
            CredentialField("url", "API URL", "url", "https://crm.example.com/api",
                            help="Volledige API root, eindigend op /api"),
            CredentialField("api_key", "JWT authtoken", "password", "eyJ0eXAi...",
                            help="JWT token uit de Themesic REST API module"),
        ],
    ),
    ProviderSpec(
        slug="moneybird", name="Moneybird", tagline="Boekhouden in de cloud",
        icon="🐦", color="bg-emerald-500", docs_url="https://developer.moneybird.com/",
        fields=[
            CredentialField("access_token", "Personal Access Token", "password", "eyJhbGciOi...",
                            help="Maak een token aan in Moneybird → Profile → Developers"),
            CredentialField("administration_id", "Administration ID", "text", "123456789012345678",
                            help="ID van de administratie die je wil koppelen"),
        ],
    ),
    ProviderSpec(
        slug="wefact", name="WeFact", tagline="Facturatie & klantadministratie",
        icon="📄", color="bg-amber-500", docs_url="https://www.wefact.nl/api/",
        fields=[
            CredentialField("api_key", "API key", "password", "...",
                            help="Te vinden in WeFact → Instellingen → API"),
        ],
    ),
    ProviderSpec(
        slug="twinfield", name="Twinfield", tagline="Wolters Kluwer accounting",
        icon="🔷", color="bg-indigo-500",
        docs_url="https://accounting.twinfield.com/webservices/documentation",
        fields=[
            CredentialField("client_id", "OAuth Client ID", "text"),
            CredentialField("client_secret", "OAuth Client Secret", "password"),
            CredentialField("refresh_token", "Refresh Token", "password"),
            CredentialField("cluster", "Cluster", "text", "eu1.twinfield.com",
                            help="Bv. eu1.twinfield.com — wordt automatisch gevonden na auth"),
            CredentialField("company_code", "Company code", "text"),
        ],
        status="beta",
    ),
    ProviderSpec(
        slug="yuki", name="Yuki", tagline="Yuki Works boekhouding",
        icon="🌸", color="bg-pink-500",
        docs_url="https://api.yukiworks.nl/docs/default.aspx",
        fields=[
            CredentialField("access_key", "API Access Key", "password",
                            help="Yuki → Instellingen → Toegang → API toegang"),
            CredentialField("administration_id", "Administration ID (GUID)", "text",
                            "00000000-0000-0000-0000-000000000000"),
        ],
        status="beta",
    ),
]


def spec_to_dict(spec: ProviderSpec) -> dict:
    return {
        "slug": spec.slug, "name": spec.name, "tagline": spec.tagline,
        "icon": spec.icon, "color": spec.color, "docs_url": spec.docs_url, "status": spec.status,
        "fields": [
            {"key": f.key, "label": f.label, "type": f.type, "placeholder": f.placeholder,
             "required": f.required, "help": f.help, "options": f.options}
            for f in spec.fields
        ],
    }


class IntegrationClient(ABC):
    PROVIDER: str = ""

    def __init__(self, credentials: dict):
        self.credentials = credentials or {}

    @abstractmethod
    async def test_connection(self) -> dict:
        ...

    async def list_customers(self) -> list[dict]:
        raise NotImplementedError(f"{self.PROVIDER}: list_customers not implemented")

    async def list_invoices(self) -> list[dict]:
        raise NotImplementedError(f"{self.PROVIDER}: list_invoices not implemented")

    async def list_payments(self) -> list[dict]:
        raise NotImplementedError(f"{self.PROVIDER}: list_payments not implemented")
