import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import get_settings
from app.models.user import User
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kvk", tags=["KvK"])
settings = get_settings()

KVK_BASE_URL = "https://api.kvk.nl/api/v2"


def _headers() -> dict:
    key = getattr(settings, "KVK_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="KvK API is niet geconfigureerd")
    return {"apikey": key, "Accept": "application/json"}


def _clean_item(item: dict) -> dict:
    """Normalize a KvK search result item to a compact frontend shape."""
    addresses = item.get("addresses", []) or []
    main = next((a for a in addresses if a.get("type") == "bezoekadres"), None) or (addresses[0] if addresses else {})
    return {
        "kvk_number": item.get("kvkNumber"),
        "branch_number": item.get("branchNumber"),
        "rsin": item.get("rsin"),
        "name": item.get("name") or item.get("tradeNames", {}).get("currentTradeNames", [None])[0],
        "type": item.get("type"),
        "street": main.get("street"),
        "house_number": main.get("houseNumber"),
        "postal_code": main.get("postalCode"),
        "city": main.get("city"),
        "country": main.get("country"),
    }


@router.get("/search")
async def search(
    q: str = Query(..., min_length=2, description="KvK nummer, handelsnaam of plaats"),
    current_user: User = Depends(get_current_user),
):
    """Zoek in het Handelsregister op naam, KvK-nummer of plaats.

    Vereist authenticatie zodat de API-key niet door anonieme gebruikers
    kan worden uitgeput.
    """
    params: dict = {}
    q = q.strip()

    if q.isdigit() and len(q) >= 7:
        params["kvkNummer"] = q
    else:
        params["naam"] = q

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{KVK_BASE_URL}/search", params=params, headers=_headers())
    except httpx.HTTPError as e:
        logger.warning(f"KvK API request failed: {e}")
        raise HTTPException(status_code=502, detail="KvK API bereikbaarheid verstoord")

    if r.status_code == 401:
        raise HTTPException(status_code=503, detail="KvK API key is ongeldig")
    if r.status_code == 404:
        return {"results": [], "total": 0}
    if r.status_code >= 400:
        logger.warning(f"KvK API returned {r.status_code}: {r.text[:200]}")
        raise HTTPException(status_code=502, detail=f"KvK API fout ({r.status_code})")

    data = r.json()
    items = data.get("resultaten", []) or []
    results = [_clean_item(i) for i in items[:15]]
    return {"results": results, "total": data.get("totaal", len(results))}


@router.get("/by-kvk/{kvk_number}")
async def by_kvk_number(
    kvk_number: str,
    current_user: User = Depends(get_current_user),
):
    """Haal basisprofiel op voor een specifiek KvK-nummer."""
    if not kvk_number.isdigit() or len(kvk_number) < 7:
        raise HTTPException(status_code=400, detail="Ongeldig KvK-nummer")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{KVK_BASE_URL}/search",
                params={"kvkNummer": kvk_number},
                headers=_headers(),
            )
    except httpx.HTTPError as e:
        logger.warning(f"KvK API request failed: {e}")
        raise HTTPException(status_code=502, detail="KvK API bereikbaarheid verstoord")

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Onderneming niet gevonden")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"KvK API fout ({r.status_code})")

    items = r.json().get("resultaten", []) or []
    if not items:
        raise HTTPException(status_code=404, detail="Onderneming niet gevonden")
    return _clean_item(items[0])
