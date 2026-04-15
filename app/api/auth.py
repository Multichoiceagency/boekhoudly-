import uuid
import random
import logging
from datetime import datetime, timedelta
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token,
    GoogleAuthRequest, OnboardingUpdate, OnboardingComplete
)
from app.utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.config import get_settings
from app.services.email_service import send_verification_email, send_welcome_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authenticatie"])
settings = get_settings()

# In-memory verification code store (use Redis in production)
_verification_codes: dict[str, dict] = {}


@router.post("/register", response_model=Token, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registreer een nieuw account met e-mail en wachtwoord."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="E-mailadres is al in gebruik")

    company = None
    if data.company_name:
        company = Company(id=uuid.uuid4(), name=data.company_name)
        db.add(company)
        await db.flush()

    user = User(
        id=uuid.uuid4(),
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        company_id=company.id if company else None,
        onboarding_completed=False,
        onboarding_step=0,
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, is_new_user=True)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Inloggen met e-mail en wachtwoord."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ongeldige inloggegevens")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, is_new_user=not user.onboarding_completed)


@router.post("/send-code")
async def send_code(request: Request, data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Stuur een verificatiecode naar het opgegeven e-mailadres."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="E-mailadres is verplicht")

    # If the Nuxt server is calling us with a valid shared secret, we let it
    # handle both rate limiting and email delivery — just generate and return
    # the code. This keeps the SMTP dependency on the Nuxt side (Vercel/Coolify).
    nuxt_secret = getattr(settings, "NUXT_INTERNAL_SECRET", "")
    incoming_secret = request.headers.get("X-Nuxt-Secret", "")
    nuxt_authenticated = bool(nuxt_secret) and incoming_secret == nuxt_secret

    # Check rate limiting (max 1 per 60 seconds) — only when not Nuxt-authenticated
    existing = _verification_codes.get(email)
    if not nuxt_authenticated and existing and datetime.utcnow() - existing["created_at"] < timedelta(seconds=60):
        raise HTTPException(status_code=429, detail="Wacht even voordat je een nieuwe code aanvraagt")

    # Generate 6-digit code
    code = f"{random.randint(100000, 999999)}"

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    is_new = user is None

    # Store code with expiry
    _verification_codes[email] = {
        "code": code,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "attempts": 0,
        "is_new": is_new,
    }

    logger.info(f"Verification code generated for {email} (new_user={is_new}, via_nuxt={nuxt_authenticated})")

    if nuxt_authenticated:
        # Nuxt will email the code itself — return it so it can
        return {"message": "Verificatiecode verzonden", "is_new_user": is_new, "code": code}

    # Fallback: send email from backend (requires SMTP to be configured)
    background_tasks.add_task(send_verification_email, email, code, not is_new)
    return {"message": "Verificatiecode verzonden", "is_new_user": is_new}


@router.post("/verify-code", response_model=Token)
async def verify_code(data: dict, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Verifieer de code en log in of registreer de gebruiker."""
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    full_name = data.get("full_name", "").strip()

    if not email or not code:
        raise HTTPException(status_code=400, detail="E-mail en code zijn verplicht")

    # Get stored code
    stored = _verification_codes.get(email)
    if not stored:
        raise HTTPException(status_code=400, detail="Geen verificatiecode gevonden. Vraag een nieuwe aan.")

    # Check expiry
    if datetime.utcnow() > stored["expires_at"]:
        del _verification_codes[email]
        raise HTTPException(status_code=400, detail="Verificatiecode is verlopen. Vraag een nieuwe aan.")

    # Check attempts (max 5)
    if stored["attempts"] >= 5:
        del _verification_codes[email]
        raise HTTPException(status_code=429, detail="Te veel pogingen. Vraag een nieuwe code aan.")

    # Verify code
    stored["attempts"] += 1
    if stored["code"] != code:
        remaining = 5 - stored["attempts"]
        raise HTTPException(status_code=400, detail=f"Ongeldige code. Nog {remaining} pogingen over.")

    # Code is valid - clean up
    del _verification_codes[email]

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    is_new = False

    if not user:
        # New user registration
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name or email.split("@")[0],
            hashed_password=None,
            onboarding_completed=False,
            onboarding_step=0,
        )
        db.add(user)
        await db.flush()
        is_new = True
        background_tasks.add_task(send_welcome_email, email, user.full_name)

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, is_new_user=is_new or not user.onboarding_completed)


@router.post("/google", response_model=Token)
async def google_auth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Login of registreer via Google OAuth."""
    # Exchange authorization code for tokens
    redirect_uri = data.redirect_uri or settings.GOOGLE_REDIRECT_URI

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Google authenticatie mislukt")

    token_data = token_response.json()

    # Get user info from Google
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Kon Google profiel niet ophalen")

    google_user = userinfo_response.json()
    google_email = google_user.get("email")
    google_id = google_user.get("id")
    google_name = google_user.get("name", google_email.split("@")[0])
    google_avatar = google_user.get("picture")

    if not google_email:
        raise HTTPException(status_code=400, detail="Geen e-mailadres ontvangen van Google")

    # Check if user exists
    result = await db.execute(select(User).where(User.email == google_email))
    user = result.scalar_one_or_none()
    is_new = False

    if user:
        # Update OAuth info if not set
        if not user.oauth_provider:
            user.oauth_provider = "google"
            user.oauth_provider_id = google_id
        if not user.avatar_url and google_avatar:
            user.avatar_url = google_avatar
        await db.flush()
    else:
        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=google_email,
            full_name=google_name,
            oauth_provider="google",
            oauth_provider_id=google_id,
            avatar_url=google_avatar,
            hashed_password=None,
            onboarding_completed=False,
            onboarding_step=0,
        )
        db.add(user)
        await db.flush()
        is_new = True

    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, is_new_user=is_new or not user.onboarding_completed)


@router.get("/google/url")
async def google_auth_url():
    """Geeft de Google OAuth URL terug voor de frontend redirect."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth is niet geconfigureerd")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Haal huidige gebruiker op."""
    return current_user


@router.post("/init-admin", response_model=Token, status_code=201)
async def init_admin(db: AsyncSession = Depends(get_db)):
    """Maak een standaard admin account aan (alleen als er nog geen admin bestaat)."""
    existing_admin = await db.execute(select(User).where(User.role == "admin"))
    if existing_admin.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Er bestaat al een admin account")

    admin = User(
        id=uuid.uuid4(),
        email="admin@boekhoudly.nl",
        hashed_password=get_password_hash("Admin123!"),
        full_name="Beheerder",
        role="admin",
        onboarding_completed=True,
        onboarding_step=5,
    )
    db.add(admin)
    await db.flush()

    token = create_access_token({"sub": str(admin.id)})
    return Token(access_token=token, is_new_user=False)


@router.put("/onboarding", response_model=UserResponse)
async def update_onboarding(
    data: OnboardingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update onboarding stap en data."""
    current_user.onboarding_step = data.step
    if data.data:
        existing_data = current_user.onboarding_data or {}
        existing_data.update(data.data)
        current_user.onboarding_data = existing_data
    await db.flush()
    return current_user


@router.post("/onboarding/complete", response_model=UserResponse)
async def complete_onboarding(
    data: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Voltooi onboarding en maak bedrijf aan."""
    # Create or update company
    if current_user.company_id:
        result = await db.execute(select(Company).where(Company.id == current_user.company_id))
        company = result.scalar_one_or_none()
        if company:
            company.name = data.company_name
            company.kvk_number = data.kvk_number
            company.btw_number = data.btw_number
            company.address = data.address
            company.city = data.city
            company.postal_code = data.postal_code
    else:
        company = Company(
            id=uuid.uuid4(),
            name=data.company_name,
            kvk_number=data.kvk_number,
            btw_number=data.btw_number,
            address=data.address,
            city=data.city,
            postal_code=data.postal_code,
        )
        db.add(company)
        await db.flush()
        current_user.company_id = company.id

    current_user.onboarding_completed = True
    current_user.onboarding_step = 5
    await db.flush()
    return current_user
