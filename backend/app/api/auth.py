import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authenticatie"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registreer een nieuw account."""
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
    )
    db.add(user)
    await db.flush()
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Inloggen en JWT token ontvangen."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ongeldige inloggegevens")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Haal huidige gebruiker op."""
    return current_user
