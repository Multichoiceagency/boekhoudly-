from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    company_id: UUID | None = None
    is_active: bool
    role: str = "user"
    avatar_url: str | None = None
    oauth_provider: str | None = None
    onboarding_completed: bool = False
    onboarding_step: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False


class OnboardingUpdate(BaseModel):
    step: int
    data: dict | None = None


class OnboardingComplete(BaseModel):
    company_name: str
    kvk_number: str | None = None
    btw_number: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    iban: str | None = None
    phone: str | None = None
    industry: str | None = None
    company_type: str | None = None  # zzp, bv, vof, etc.
    fiscal_year_start: str | None = None  # e.g., "01-01"
