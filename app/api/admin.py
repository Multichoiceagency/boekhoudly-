import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.auth import get_password_hash, get_current_user
from app.services.email_service import send_welcome_email

router = APIRouter(prefix="/admin", tags=["Admin"])


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen admins hebben toegang")
    return current_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lijst van alle gebruikers (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: dict,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Maak een nieuwe gebruiker aan (admin only)."""
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    role = data.get("role", "user")
    password = data.get("password", "")

    if not email or not full_name:
        raise HTTPException(status_code=400, detail="Email en naam zijn verplicht")

    if role not in ("user", "admin", "accountant"):
        raise HTTPException(status_code=400, detail="Ongeldige rol")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="E-mailadres is al in gebruik")

    user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password) if password else None,
        role=role,
        company_id=admin.company_id,
        onboarding_completed=True,
        onboarding_step=5,
    )
    db.add(user)
    await db.flush()

    # Send welcome email in background (best-effort)
    try:
        send_welcome_email(email, full_name)
    except Exception:
        pass

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: dict,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update een gebruiker (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    if "full_name" in data:
        user.full_name = data["full_name"]
    if "role" in data and data["role"] in ("user", "admin", "accountant"):
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "password" in data and data["password"]:
        user.hashed_password = get_password_hash(data["password"])

    await db.flush()
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Verwijder een gebruiker (admin only)."""
    if str(admin.id) == user_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet verwijderen")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    await db.delete(user)
    await db.flush()
    return {"message": "Gebruiker verwijderd"}
