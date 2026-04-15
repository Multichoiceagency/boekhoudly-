"""Yuki client — SOAP API with API access key. Stub implementation that
validates the access key via the Authenticate SOAP method."""
import httpx
from app.services.integrations.base import IntegrationClient


class YukiClient(IntegrationClient):
    PROVIDER = "yuki"
    SOAP_URL = "https://api.yukiworks.nl/ws/Accounting.asmx"

    async def test_connection(self) -> dict:
        access_key = self.credentials.get("access_key")
        if not access_key:
            return {"status": "error", "message": "Access key ontbreekt"}

        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <Authenticate xmlns="http://www.theyukicompany.com/">
      <accessKey>{access_key}</accessKey>
    </Authenticate>
  </soap12:Body>
</soap12:Envelope>"""

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    self.SOAP_URL,
                    content=envelope,
                    headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                )
            if r.status_code != 200 or "AuthenticateResult" not in r.text:
                return {"status": "error", "message": "Yuki Authenticate gefaald"}
            return {"status": "connected", "message": "Yuki access key geldig"}
        except httpx.HTTPError as e:
            return {"status": "error", "message": f"Verbinding mislukt: {str(e)[:150]}"}
