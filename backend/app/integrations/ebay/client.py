import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import EbayAPIError

EBAY_API_BASE = "https://api.sandbox.ebay.com" if settings.ebay_sandbox else "https://api.ebay.com"
EBAY_AUTH_BASE = (
    "https://auth.sandbox.ebay.com" if settings.ebay_sandbox else "https://auth.ebay.com"
)


class EbayClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = EBAY_API_BASE
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def close(self):
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _request(self, method: str, url: str, **kwargs) -> dict:
        response = await self._client.request(method, url, **kwargs)

        if response.status_code == 429:
            raise EbayAPIError("Rate limit exceeded", is_transient=True)
        if response.status_code >= 500:
            raise EbayAPIError(
                f"eBay server error: {response.status_code}", is_transient=True
            )
        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            errors = error_data.get("errors", [{}])
            msg = errors[0].get("message", f"HTTP {response.status_code}") if errors else f"HTTP {response.status_code}"
            error_id = errors[0].get("errorId") if errors else None
            raise EbayAPIError(msg, error_id=str(error_id) if error_id else None)

        if response.status_code == 204:
            return {}
        return response.json()

    async def get(self, url: str, **kwargs) -> dict:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> dict:
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> dict:
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> dict:
        return await self._request("DELETE", url, **kwargs)
