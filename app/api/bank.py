import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.bank_connection import BankConnection
from app.services.bank_service import bank_service
from app.utils.auth import get_current_user
from app.config import get_settings
from pydantic import BaseModel

# GoCardless status code mapping to internal statuses
GOCARDLESS_STATUS_MAP = {
    "CR": "pending",    # Created
    "GC": "pending",    # Giving consent
    "UA": "pending",    # Undergoing authentication
    "GA": "pending",    # Granting access
    "SA": "pending",    # Selecting accounts
    "QA": "pending",    # Queued for authentication
    "LN": "linked",     # Linked
    "EX": "expired",    # Expired
    "RJ": "error",      # Rejected
    "ER": "error",      # Error
    "SU": "linked",     # Suspended (still has data)
    "ID": "error",      # Invalid
}

router = APIRouter(prefix="/bank", tags=["Bank Integratie"])
settings = get_settings()


class InstitutionResponse(BaseModel):
    id: str
    name: str
    logo: str | None = None
    bic: str | None = None
    countries: list[str] = []


class CreateConnectionRequest(BaseModel):
    institution_id: str
    institution_name: str
    institution_logo: str | None = None


class ConnectionResponse(BaseModel):
    id: str
    institution_name: str
    institution_logo: str | None = None
    iban: str | None = None
    account_name: str | None = None
    status: str
    last_synced: str | None = None

    model_config = {"from_attributes": True}


@router.get("/institutions")
async def list_institutions(
    country: str = Query(default="NL", description="Land code (NL, BE, DE, etc.)"),
    current_user: User = Depends(get_current_user),
):
    """Haal beschikbare banken op voor een land."""
    if not settings.GOCARDLESS_SECRET_ID:
        raise HTTPException(status_code=500, detail="Bank integratie is niet geconfigureerd")

    try:
        institutions = await bank_service.get_institutions(country)
        return [
            {
                "id": inst["id"],
                "name": inst["name"],
                "logo": inst.get("logo"),
                "bic": inst.get("bic"),
                "countries": inst.get("countries", []),
            }
            for inst in institutions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fout bij ophalen banken: {str(e)}")


@router.post("/connect")
async def create_connection(
    data: CreateConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start een bankkoppeling - geeft een redirect URL terug."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Je moet eerst een bedrijf aanmaken")

    try:
        reference = f"ff-{current_user.company_id}-{uuid.uuid4().hex[:8]}"
        redirect_url = f"{settings.FRONTEND_URL}/bank/callback"

        requisition = await bank_service.create_requisition(
            institution_id=data.institution_id,
            redirect_url=redirect_url,
            reference=reference,
        )

        # Store connection in database
        connection = BankConnection(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            institution_id=data.institution_id,
            institution_name=data.institution_name,
            institution_logo=data.institution_logo,
            requisition_id=requisition["id"],
            status="pending",
        )
        db.add(connection)
        await db.commit()

        return {
            "connection_id": str(connection.id),
            "link": requisition["link"],
            "requisition_id": requisition["id"],
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Fout bij aanmaken bankkoppeling: {str(e)}")


@router.post("/callback")
async def bank_callback(
    requisition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verwerk de callback na bank autorisatie."""
    result = await db.execute(
        select(BankConnection).where(BankConnection.requisition_id == requisition_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Bankkoppeling niet gevonden")

    # Security: validate connection belongs to user's company
    if connection.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Geen toegang tot deze bankkoppeling")

    try:
        # Get requisition status from GoCardless
        requisition = await bank_service.get_requisition(requisition_id)
        gc_status = requisition.get("status", "ER")

        if gc_status == "LN":  # Linked
            accounts = requisition.get("accounts", [])
            if accounts:
                account_id = accounts[0]  # Use first account

                # Get account details
                details = await bank_service.get_account_details(account_id)
                account_data = details.get("account", {})

                connection.account_id = account_id
                connection.iban = account_data.get("iban")
                connection.account_name = account_data.get("ownerName", account_data.get("name", "Hoofdrekening"))
                connection.status = "linked"
            else:
                connection.status = "error"
                connection.metadata = {"error": "Geen accounts gevonden"}
        else:
            connection.status = GOCARDLESS_STATUS_MAP.get(gc_status, "error")

        await db.commit()

        return {
            "status": connection.status,
            "iban": connection.iban,
            "account_name": connection.account_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        connection.status = "error"
        connection.metadata = {"error": str(e)}
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Fout bij verwerken callback: {str(e)}")


@router.get("/connections")
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Haal alle bankkoppelingen op voor het huidige bedrijf."""
    if not current_user.company_id:
        return []

    result = await db.execute(
        select(BankConnection)
        .where(BankConnection.company_id == current_user.company_id)
        .where(BankConnection.is_active == True)
    )
    connections = result.scalars().all()

    return [
        {
            "id": str(conn.id),
            "institution_name": conn.institution_name,
            "institution_logo": conn.institution_logo,
            "iban": conn.iban,
            "account_name": conn.account_name,
            "status": conn.status,
            "last_synced": conn.last_synced.isoformat() if conn.last_synced else None,
        }
        for conn in connections
    ]


@router.post("/sync/{connection_id}")
async def sync_transactions(
    connection_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Synchroniseer transacties van een gekoppelde bankrekening."""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Bankkoppeling niet gevonden")

    if connection.status != "linked" or not connection.account_id:
        raise HTTPException(status_code=400, detail="Bankrekening is niet gekoppeld")

    try:
        transactions = await bank_service.get_transactions(
            account_id=connection.account_id,
            date_from=date_from,
            date_to=date_to,
        )

        # Update last synced
        connection.last_synced = datetime.utcnow()
        await db.commit()

        # Return raw transactions for now - the frontend/AI can process them
        booked = transactions.get("transactions", {}).get("booked", [])
        pending = transactions.get("transactions", {}).get("pending", [])

        return {
            "booked": booked,
            "pending": pending,
            "count": len(booked) + len(pending),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fout bij synchroniseren: {str(e)}")


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verwijder een bankkoppeling."""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Bankkoppeling niet gevonden")

    # Try to revoke at GoCardless
    try:
        await bank_service.delete_requisition(connection.requisition_id)
    except Exception:
        pass  # Best effort

    connection.is_active = False
    connection.status = "revoked"
    await db.commit()

    return {"message": "Bankkoppeling verwijderd"}
