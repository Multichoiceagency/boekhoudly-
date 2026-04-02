from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./fiscalflow.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "fiscalflow-documents"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    JWT_SECRET: str = "change-this-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback/google"

    # GoCardless (Nordigen) Bank Integration
    GOCARDLESS_SECRET_ID: str = ""
    GOCARDLESS_SECRET_KEY: str = ""
    GOCARDLESS_BASE_URL: str = "https://bankaccountdata.gocardless.com/api/v2"

    # Email / SMTP (TransIP: SSL on port 465)
    MAIL_HOST: str = "smtp.transip.email"
    MAIL_PORT: int = 465
    MAIL_FROM: str = "info@fiscaalflow.nl"
    MAIL_PASSWORD: str = ""
    MAIL_FROM_NAME: str = "FiscalFlow"
    MAIL_USE_SSL: bool = True

    # Perfex CRM Integration
    PERFEX_CRM_URL: str = ""  # e.g. https://crm.example.com
    PERFEX_CRM_API_KEY: str = ""

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Google Drive
    GOOGLE_DRIVE_CLIENT_ID: str = ""
    GOOGLE_DRIVE_CLIENT_SECRET: str = ""
    GOOGLE_DRIVE_REDIRECT_URI: str = "http://localhost:3000/integrations/callback/google-drive"

    # Dropbox
    DROPBOX_APP_KEY: str = ""
    DROPBOX_APP_SECRET: str = ""
    DROPBOX_REDIRECT_URI: str = "http://localhost:3000/integrations/callback/dropbox"

    # OneDrive (Microsoft)
    ONEDRIVE_CLIENT_ID: str = ""
    ONEDRIVE_CLIENT_SECRET: str = ""
    ONEDRIVE_REDIRECT_URI: str = "http://localhost:3000/integrations/callback/onedrive"
    ONEDRIVE_TENANT_ID: str = "common"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
