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


def _clean_search_item(item: dict) -> dict:
    """Normalize a /zoeken result. Search only has straatnaam+plaats, no postcode."""
    adres = (item.get("adres") or {}).get("binnenlandsAdres") or (item.get("adres") or {}).get("buitenlandsAdres") or {}
    return {
        "kvk_number": item.get("kvkNummer"),
        "branch_number": item.get("vestigingsnummer"),
        "rsin": None,
        "name": item.get("naam"),
        "type": item.get("type"),
        "street": adres.get("straatnaam"),
        "house_number": "",
        "postal_code": None,
        "city": adres.get("plaats"),
        "country": "Nederland",
    }


def _extract_address(adressen: list) -> dict:
    """Pick the best address from a list of KvK adressen — prefer bezoekadres."""
    if not adressen:
        return {}
    bezoek = next((a for a in adressen if a.get("type") == "bezoekadres"), None)
    return bezoek or adressen[0]


def _clean_profile(d: dict) -> dict:
    """Normalize a /basisprofielen response with full address info."""
    hoofd = (d.get("_embedded") or {}).get("hoofdvestiging") or {}
    address = _extract_address(hoofd.get("adressen") or [])
    return {
        "kvk_number": d.get("kvkNummer"),
        "branch_number": hoofd.get("vestigingsnummer"),
        "rsin": d.get("rsin"),
        "name": d.get("naam") or d.get("statutaireNaam") or hoofd.get("eersteHandelsnaam"),
        "type": "Hoofdvestiging" if hoofd.get("indHoofdvestiging") == "Ja" else None,
        "street": address.get("straatnaam"),
        "house_number": str(address.get("huisnummer") or "") + (address.get("huisletter") or "") + (address.get("huisnummerToevoeging") or ""),
        "postal_code": address.get("postcode"),
        "city": address.get("plaats"),
        "country": address.get("land") or "Nederland",
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
    results = [_clean_search_item(i) for i in items[:15]]
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

    return _clean_profile(r.json())
