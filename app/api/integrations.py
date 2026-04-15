"""Generic per-company integration management.

Each company can have one connection per provider (perfex, moneybird, wefact,
twinfield, yuki). Credentials are stored in integration_connections.

Permission model:
- admin: can manage connections for any company
- accountant: can manage connections for companies they own
- user: can manage connections for their own company

Frontend uses these endpoints from /instellingen/integraties to add/test/
remove connections. The data-fetching endpoints under /api/integrations/{id}
proxy to the right provider client.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.integration_connection import IntegrationConnection
from app.models.company_subscription import CompanySubscription
from app.utils.auth import get_current_user
from app.services.integrations import get_client, PROVIDERS
from app.services.integrations.base import spec_to_dict

router = APIRouter(prefix="/integrations", tags=["Integrations"])


def _can_manage_company(user: User, company_id: uuid.UUID, accountant_id: uuid.UUID | None = None) -> bool:
    if user.role == "admin":
        return True
    if user.role == "accountant" and accountant_id and accountant_id == user.id:
        return True
    if user.company_id == company_id:
        return True
    return False


def _conn_to_dict(conn: IntegrationConnection, include_secrets: bool = False) -> dict:
    creds = conn.credentials or {}
    if not include_secrets:
        # Mask secret-looking values
        creds = {
            k: ("***" if any(s in k.lower() for s in ("key", "token", "secret", "pass")) else v)
            for k, v in creds.items()
        }
    return {
        "id": str(conn.id),
        "company_id": str(conn.company_id),
        "provider": conn.provider,
        "name": conn.name,
        "credentials": creds,
        "status": conn.status,
        "last_error": conn.last_error,
        "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        "metadata": conn.metadata_json or {},
        "created_at": conn.created_at.isoformat() if conn.created_at else None,
        "updated_at": conn.updated_at.isoformat() if conn.updated_at else None,
    }


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user)):
    """List all available integration providers (Perfex/Moneybird/WeFact/Twinfield/Yuki)."""
    return [spec_to_dict(p) for p in PROVIDERS]


@router.get("")
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all integration connections visible to the current user."""
    q = select(IntegrationConnection)
    if current_user.role == "admin":
        pass
    elif current_user.role == "accountant":
        # See connections for own companies + own home company
        sub_ids_result = await db.execute(
            select(CompanySubscription.company_id).where(CompanySubscription.accountant_id == current_user.id)
        )
        ids = [r[0] for r in sub_ids_result.all()]
        if current_user.company_id and current_user.company_id not in ids:
            ids.append(current_user.company_id)
        if not ids:
            return []
        q = q.where(IntegrationConnection.company_id.in_(ids))
    else:
        if not current_user.company_id:
            return []
        q = q.where(IntegrationConnection.company_id == current_user.company_id)

    q = q.order_by(IntegrationConnection.created_at.desc())
    result = await db.execute(q)
    return [_conn_to_dict(c) for c in result.scalars().all()]


@router.post("", status_code=201)
async def create_or_update_connection(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new connection or update credentials for an existing one.

    Body:
      - provider: 'perfex' | 'moneybird' | 'wefact' | 'twinfield' | 'yuki'
      - credentials: dict with provider-specific fields
      - name: optional friendly label
      - company_id: optional, defaults to current user's company
    """
    provider = data.get("provider")
    credentials = data.get("credentials") or {}
    if not provider:
        raise HTTPException(status_code=400, detail="provider is verplicht")
    if not any(p.slug == provider for p in PROVIDERS):
        raise HTTPException(status_code=400, detail=f"Onbekende provider: {provider}")

    company_id_raw = data.get("company_id") or (str(current_user.company_id) if current_user.company_id else None)
    if not company_id_raw:
        raise HTTPException(status_code=400, detail="company_id is verplicht (gebruiker heeft geen bedrijf)")
    company_id = uuid.UUID(company_id_raw)

    if not _can_manage_company(current_user, company_id):
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bedrijf")

    # Upsert: one connection per (company, provider)
    existing = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider == provider,
        )
    )
    conn = existing.scalar_one_or_none()

    if conn:
        conn.credentials = credentials
        if "name" in data:
            conn.name = data["name"]
        conn.status = "unknown"
        conn.last_error = None
        conn.updated_at = datetime.utcnow()
    else:
        conn = IntegrationConnection(
            id=uuid.uuid4(),
            company_id=company_id,
            provider=provider,
            name=data.get("name"),
            credentials=credentials,
            status="unknown",
        )
        db.add(conn)

    await db.flush()
    return _conn_to_dict(conn)


@router.delete("/{conn_id}")
async def delete_connection(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Niet gevonden")
    if not _can_manage_company(current_user, conn.company_id):
        raise HTTPException(status_code=403, detail="Geen toegang")
    await db.delete(conn)
    await db.flush()
    return {"status": "deleted"}


@router.post("/{conn_id}/test")
async def test_connection(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Niet gevonden")
    if not _can_manage_company(current_user, conn.company_id):
        raise HTTPException(status_code=403, detail="Geen toegang")

    try:
        client = get_client(conn.provider, conn.credentials)
        result = await client.test_connection()
    except Exception as e:
        result = {"status": "error", "message": str(e)[:200]}

    conn.status = result.get("status", "unknown")
    conn.last_error = result.get("message") if result.get("status") != "connected" else None
    if result.get("metadata"):
        conn.metadata_json = result["metadata"]
    conn.updated_at = datetime.utcnow()
    await db.flush()
    return result


@router.post("/test-credentials")
async def test_credentials(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """Test arbitrary credentials without saving them — used by the connect modal."""
    provider = data.get("provider")
    credentials = data.get("credentials") or {}
    if not provider:
        raise HTTPException(status_code=400, detail="provider is verplicht")
    try:
        client = get_client(provider, credentials)
        return await client.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}


@router.get("/{conn_id}/customers")
async def get_customers(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await _load_conn(conn_id, current_user, db)
    return await get_client(conn.provider, conn.credentials).list_customers()


@router.get("/{conn_id}/invoices")
async def get_invoices(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await _load_conn(conn_id, current_user, db)
    return await get_client(conn.provider, conn.credentials).list_invoices()


@router.get("/{conn_id}/payments")
async def get_payments(
    conn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conn = await _load_conn(conn_id, current_user, db)
    return await get_client(conn.provider, conn.credentials).list_payments()


async def _load_conn(conn_id: str, user: User, db: AsyncSession) -> IntegrationConnection:
    result = await db.execute(select(IntegrationConnection).where(IntegrationConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Niet gevonden")
    if not _can_manage_company(user, conn.company_id):
        raise HTTPException(status_code=403, detail="Geen toegang")
    return conn
