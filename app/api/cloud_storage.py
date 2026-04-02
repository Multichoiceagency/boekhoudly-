import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.cloud_connection import CloudConnection
from app.services.cloud_storage_service import google_drive_service, dropbox_service, onedrive_service
from app.utils.auth import get_current_user
from app.config import get_settings
from pydantic import BaseModel

router = APIRouter(prefix="/cloud", tags=["Cloud Opslag"])
settings = get_settings()

PROVIDER_SERVICES = {
    "google_drive": google_drive_service,
    "dropbox": dropbox_service,
    "onedrive": onedrive_service,
}

PROVIDER_LABELS = {
    "google_drive": "Google Drive",
    "dropbox": "Dropbox",
    "onedrive": "OneDrive",
}


class ConnectRequest(BaseModel):
    code: str
    provider: str  # google_drive, dropbox, onedrive


class SyncSettingsRequest(BaseModel):
    sync_folder_id: str | None = None
    sync_folder_name: str | None = None
    auto_import: bool = False


class ImportFileRequest(BaseModel):
    file_id: str
    file_name: str
    file_path: str | None = None  # For Dropbox


# === Auth URLs ===

@router.get("/auth-url/{provider}")
async def get_auth_url(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    """Get OAuth authorization URL for a cloud storage provider."""
    state = f"{provider}:{current_user.id}"

    if provider == "google_drive":
        if not settings.GOOGLE_DRIVE_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Google Drive is niet geconfigureerd")
        return {"url": google_drive_service.get_auth_url(state)}
    elif provider == "dropbox":
        if not settings.DROPBOX_APP_KEY:
            raise HTTPException(status_code=500, detail="Dropbox is niet geconfigureerd")
        return {"url": dropbox_service.get_auth_url(state)}
    elif provider == "onedrive":
        if not settings.ONEDRIVE_CLIENT_ID:
            raise HTTPException(status_code=500, detail="OneDrive is niet geconfigureerd")
        return {"url": onedrive_service.get_auth_url(state)}
    else:
        raise HTTPException(status_code=400, detail=f"Onbekende provider: {provider}")


# === OAuth Callback ===

@router.post("/connect")
async def connect_provider(
    data: ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Exchange OAuth code and create cloud connection."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Je moet eerst een bedrijf aanmaken")

    service = PROVIDER_SERVICES.get(data.provider)
    if not service:
        raise HTTPException(status_code=400, detail=f"Onbekende provider: {data.provider}")

    try:
        # Exchange code for tokens
        token_data = await service.exchange_code(data.code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Get user info from provider
        user_info = await service.get_user_info(access_token)

        # Check if connection already exists
        result = await db.execute(
            select(CloudConnection).where(
                CloudConnection.company_id == current_user.company_id,
                CloudConnection.provider == data.provider,
                CloudConnection.is_active == True,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing connection
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing.provider_account_id = user_info.get("id")
            existing.provider_email = user_info.get("email")
            existing.provider_name = user_info.get("name")
            existing.status = "active"
            await db.commit()
            connection = existing
        else:
            # Create new connection
            connection = CloudConnection(
                id=uuid.uuid4(),
                company_id=current_user.company_id,
                user_id=current_user.id,
                provider=data.provider,
                provider_account_id=user_info.get("id"),
                provider_email=user_info.get("email"),
                provider_name=user_info.get("name"),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                status="active",
            )
            db.add(connection)
            await db.commit()

        return {
            "id": str(connection.id),
            "provider": data.provider,
            "provider_label": PROVIDER_LABELS.get(data.provider, data.provider),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "status": "active",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Koppeling mislukt: {str(e)}")


# === List Connections ===

@router.get("/connections")
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active cloud storage connections."""
    if not current_user.company_id:
        return []

    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.company_id == current_user.company_id,
            CloudConnection.is_active == True,
        )
    )
    connections = result.scalars().all()

    return [
        {
            "id": str(conn.id),
            "provider": conn.provider,
            "provider_label": PROVIDER_LABELS.get(conn.provider, conn.provider),
            "email": conn.provider_email,
            "name": conn.provider_name,
            "status": conn.status,
            "auto_import": conn.auto_import,
            "sync_folder_name": conn.sync_folder_name,
            "files_imported": conn.files_imported,
            "last_synced": conn.last_synced.isoformat() if conn.last_synced else None,
        }
        for conn in connections
    ]


# === Helper: get valid access token ===

async def _get_valid_token(connection: CloudConnection, db: AsyncSession) -> str:
    """Get a valid access token, refreshing if needed."""
    if connection.token_expires_at and connection.token_expires_at > datetime.utcnow():
        return connection.access_token

    # Need to refresh
    service = PROVIDER_SERVICES.get(connection.provider)
    if not service or not connection.refresh_token:
        raise HTTPException(status_code=400, detail="Token verlopen, koppel opnieuw")

    try:
        token_data = await service.refresh_access_token(connection.refresh_token)
        connection.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            connection.refresh_token = token_data["refresh_token"]
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
        await db.commit()
        return connection.access_token
    except Exception:
        connection.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Token verlopen, koppel opnieuw")


# === Browse Files ===

@router.get("/files/{connection_id}")
async def list_files(
    connection_id: str,
    folder_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List files from a cloud storage connection."""
    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.id == connection_id,
            CloudConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Koppeling niet gevonden")

    access_token = await _get_valid_token(connection, db)
    service = PROVIDER_SERVICES.get(connection.provider)

    try:
        if connection.provider == "google_drive":
            data = await service.list_files(access_token, folder_id)
            return {
                "files": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "type": "folder" if f["mimeType"] == "application/vnd.google-apps.folder" else "file",
                        "size": f.get("size"),
                        "modified": f.get("modifiedTime"),
                        "mime_type": f.get("mimeType"),
                    }
                    for f in data.get("files", [])
                ]
            }
        elif connection.provider == "dropbox":
            path = folder_id or ""
            data = await service.list_files(access_token, path)
            return data
        elif connection.provider == "onedrive":
            data = await service.list_files(access_token, folder_id)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fout bij ophalen bestanden: {str(e)}")


# === List Folders ===

@router.get("/folders/{connection_id}")
async def list_folders(
    connection_id: str,
    folder_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List folders from a cloud storage connection (for sync folder selection)."""
    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.id == connection_id,
            CloudConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Koppeling niet gevonden")

    access_token = await _get_valid_token(connection, db)
    service = PROVIDER_SERVICES.get(connection.provider)

    try:
        if connection.provider == "google_drive":
            folders = await service.list_folders(access_token)
            return [{"id": f["id"], "name": f["name"]} for f in folders]
        elif connection.provider == "dropbox":
            folders = await service.list_folders(access_token, folder_id or "")
            return [{"id": f["path"], "name": f["name"]} for f in folders]
        elif connection.provider == "onedrive":
            folders = await service.list_folders(access_token, folder_id)
            return [{"id": f["id"], "name": f["name"]} for f in folders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fout bij ophalen mappen: {str(e)}")


# === Import File ===

@router.post("/import/{connection_id}")
async def import_file(
    connection_id: str,
    data: ImportFileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import a file from cloud storage into FiscalFlow for processing."""
    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.id == connection_id,
            CloudConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Koppeling niet gevonden")

    access_token = await _get_valid_token(connection, db)
    service = PROVIDER_SERVICES.get(connection.provider)

    try:
        # Download file from cloud
        if connection.provider == "dropbox" and data.file_path:
            content = await service.download_file(access_token, data.file_path)
        else:
            content = await service.download_file(access_token, data.file_id)

        # Upload to MinIO via existing storage service
        from app.services.storage_service import storage_service
        file_url = await storage_service.upload_file(
            file_content=content,
            file_name=data.file_name,
            company_id=str(current_user.company_id),
        )

        # Create document record for processing
        from app.models.document import Document
        document = Document(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            file_url=file_url,
            file_name=data.file_name,
            file_type=data.file_name.split(".")[-1].lower() if "." in data.file_name else "unknown",
            processing_status="uploaded",
        )
        db.add(document)

        # Update import count
        connection.files_imported = (connection.files_imported or 0) + 1
        connection.last_synced = datetime.utcnow()
        await db.commit()

        return {
            "document_id": str(document.id),
            "file_name": data.file_name,
            "status": "uploaded",
            "message": f"Bestand geimporteerd vanuit {PROVIDER_LABELS.get(connection.provider, connection.provider)}",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import mislukt: {str(e)}")


# === Update Sync Settings ===

@router.put("/sync/{connection_id}")
async def update_sync_settings(
    connection_id: str,
    data: SyncSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update auto-sync settings for a cloud connection."""
    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.id == connection_id,
            CloudConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Koppeling niet gevonden")

    connection.sync_folder_id = data.sync_folder_id
    connection.sync_folder_name = data.sync_folder_name
    connection.auto_import = data.auto_import
    await db.commit()

    return {"message": "Sync instellingen bijgewerkt"}


# === Disconnect ===

@router.delete("/connections/{connection_id}")
async def disconnect_provider(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a cloud storage provider."""
    result = await db.execute(
        select(CloudConnection).where(
            CloudConnection.id == connection_id,
            CloudConnection.company_id == current_user.company_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Koppeling niet gevonden")

    connection.is_active = False
    connection.status = "revoked"
    connection.access_token = None
    connection.refresh_token = None
    await db.commit()

    return {"message": f"{PROVIDER_LABELS.get(connection.provider, connection.provider)} ontkoppeld"}
