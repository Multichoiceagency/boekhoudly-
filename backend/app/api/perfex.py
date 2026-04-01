from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.perfex_service import PerfexCRMClient

router = APIRouter(prefix="/perfex", tags=["Perfex CRM"])


@router.post("/test")
async def test_connection(data: dict, current_user: User = Depends(get_current_user)):
    """Test Perfex CRM connection with provided URL and API key."""
    url = data.get("url", "").strip()
    api_key = data.get("api_key", "").strip()
    if not url or not api_key:
        raise HTTPException(status_code=400, detail="URL en API key zijn verplicht")
    try:
        client = PerfexCRMClient(base_url=url, api_key=api_key)
        result = await client.test_connection()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/sync")
async def sync_all_data(data: dict, current_user: User = Depends(get_current_user)):
    """Sync all data from Perfex CRM."""
    url = data.get("url", "").strip()
    api_key = data.get("api_key", "").strip()
    if not url or not api_key:
        raise HTTPException(status_code=400, detail="URL en API key zijn verplicht")
    try:
        client = PerfexCRMClient(base_url=url, api_key=api_key)
        result = await client.sync_all()
        counts = {k: len(v) for k, v in result.items()}
        return {"status": "success", "data": result, "counts": counts}
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync mislukt: {str(e)}")


@router.post("/customers")
async def get_customers(data: dict, current_user: User = Depends(get_current_user)):
    """Get customers from Perfex CRM."""
    client = PerfexCRMClient(base_url=data.get("url"), api_key=data.get("api_key"))
    return await client.get_customers()


@router.post("/invoices")
async def get_invoices(data: dict, current_user: User = Depends(get_current_user)):
    """Get invoices from Perfex CRM."""
    client = PerfexCRMClient(base_url=data.get("url"), api_key=data.get("api_key"))
    return await client.get_invoices()


@router.post("/expenses")
async def get_expenses(data: dict, current_user: User = Depends(get_current_user)):
    """Get expenses from Perfex CRM."""
    client = PerfexCRMClient(base_url=data.get("url"), api_key=data.get("api_key"))
    return await client.get_expenses()


@router.post("/payments")
async def get_payments(data: dict, current_user: User = Depends(get_current_user)):
    """Get payments from Perfex CRM."""
    client = PerfexCRMClient(base_url=data.get("url"), api_key=data.get("api_key"))
    return await client.get_payments()
