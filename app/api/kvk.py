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
KVK_PROFILE_URL = "https://api.kvk.nl/api/v1"


def _headers() -> dict:
    key = getattr(settings, "KVK_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="KvK API is niet geconfigureerd")
    return {"apikey": key, "Accept": "application/json"}


def _clean_item(item: dict) -> dict:
    """Normalize a KvK search result (Dutch field names) to a compact frontend shape."""
    adressen = item.get("adressen", []) or []
    main = adressen[0] if adressen else {}
    return {
        "kvk_number": item.get("kvkNummer"),
        "branch_number": item.get("vestigingsnummer"),
        "rsin": item.get("rsin"),
        "name": item.get("handelsnaam") or item.get("naam"),
        "type": item.get("type"),
        "street": main.get("straatnaam"),
        "house_number": str(main.get("huisnummer", "") or "") + (main.get("huisletter") or "") + (main.get("huisnummerToevoeging") or ""),
        "postal_code": main.get("postcode"),
        "city": main.get("plaats"),
        "country": main.get("land") or "Nederland",
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
            r = await client.get(f"{KVK_BASE_URL}/zoeken", params=params, headers=_headers())
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
    """Haal basisprofiel op voor een specifiek KvK-nummer via /api/v1/basisprofielen."""
    if not kvk_number.isdigit() or len(kvk_number) < 7:
        raise HTTPException(status_code=400, detail="Ongeldig KvK-nummer")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{KVK_PROFILE_URL}/basisprofielen/{kvk_number}",
                headers=_headers(),
            )
    except httpx.HTTPError as e:
        logger.warning(f"KvK API request failed: {e}")
        raise HTTPException(status_code=502, detail="KvK API bereikbaarheid verstoord")

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Onderneming niet gevonden")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"KvK API fout ({r.status_code})")

    # basisprofielen has a different shape — extract main vestiging
    d = r.json()
    handelsnaam = d.get("handelsnaam") or (d.get("_embedded", {}).get("hoofdvestiging", {}) or {}).get("naam")
    vestiging = (d.get("_embedded", {}).get("hoofdvestiging", {}) or {})
    adressen = vestiging.get("adressen", []) or []
    main = adressen[0] if adressen else {}
    return {
        "kvk_number": d.get("kvkNummer"),
        "branch_number": vestiging.get("vestigingsnummer"),
        "rsin": d.get("rsin"),
        "name": handelsnaam,
        "type": vestiging.get("indHoofdvestiging") and "Hoofdvestiging" or None,
        "street": main.get("straatnaam"),
        "house_number": str(main.get("huisnummer", "") or "") + (main.get("huisletter") or "") + (main.get("huisnummerToevoeging") or ""),
        "postal_code": main.get("postcode"),
        "city": main.get("plaats"),
        "country": main.get("land") or "Nederland",
    }
