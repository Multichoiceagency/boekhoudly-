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
        status="stable",
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
        status="stable",
    ),
    ProviderSpec(
        slug="snelstart", name="SnelStart", tagline="Boekingen, relaties en BTW-aangiftes",
        icon="⚡", color="bg-orange-500",
        docs_url="https://b2bapi-developer.snelstart.nl/",
        fields=[
            CredentialField("client_key", "Client Key", "password",
                            help="SnelStart B2B API client key"),
            CredentialField("subscription_key", "Subscription Key", "password",
                            help="SnelStart B2B API subscription key"),
        ],
        status="stable",
    ),
    ProviderSpec(
        slug="woocommerce", name="WooCommerce", tagline="WordPress webshop bestellingen en producten",
        icon="🛒", color="bg-purple-600",
        docs_url="https://woocommerce.github.io/woocommerce-rest-api-docs/",
        fields=[
            CredentialField("url", "Shop URL", "url", "https://mijnshop.nl",
                            help="Volledige URL van je WordPress/WooCommerce shop"),
            CredentialField("consumer_key", "Consumer Key", "password", "ck_...",
                            help="WooCommerce → Instellingen → REST API"),
            CredentialField("consumer_secret", "Consumer Secret", "password", "cs_..."),
        ],
    ),
    ProviderSpec(
        slug="shopify", name="Shopify", tagline="Shopify bestellingen, klanten en producten",
        icon="🟢", color="bg-green-600",
        docs_url="https://shopify.dev/docs/api",
        fields=[
            CredentialField("shop_url", "Shop URL", "url", "mijnshop.myshopify.com",
                            help="Je Shopify winkel-URL"),
            CredentialField("access_token", "Admin API Access Token", "password",
                            help="Shopify Admin → Apps → Develop apps → Access token"),
        ],
    ),
    ProviderSpec(
        slug="magento", name="Magento / Adobe Commerce", tagline="Bestellingen en producten uit Magento",
        icon="🟧", color="bg-orange-600",
        docs_url="https://developer.adobe.com/commerce/webapi/rest/",
        fields=[
            CredentialField("url", "Magento API URL", "url", "https://mijnshop.nl/rest/V1",
                            help="Magento REST API base URL"),
            CredentialField("access_token", "Bearer Token", "password",
                            help="Magento Admin → System → Integrations → Access Token"),
        ],
        status="stable",
    ),
    ProviderSpec(
        slug="wix", name="Wix", tagline="Wix eCommerce bestellingen",
        icon="🌐", color="bg-black",
        docs_url="https://dev.wix.com/docs/rest",
        fields=[
            CredentialField("api_key", "API Key", "password",
                            help="Wix → Developer Center → API Keys"),
            CredentialField("site_id", "Site ID", "text",
                            help="Je Wix site ID"),
        ],
        status="stable",
    ),
    ProviderSpec(
        slug="medusa", name="Medusa", tagline="Open-source headless commerce",
        icon="🟣", color="bg-violet-600",
        docs_url="https://docs.medusajs.com/api/admin",
        fields=[
            CredentialField("url", "Medusa API URL", "url", "https://api.mijnshop.nl",
                            help="URL van je Medusa backend"),
            CredentialField("api_key", "API Key", "password",
                            help="Medusa Admin API key"),
        ],
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
