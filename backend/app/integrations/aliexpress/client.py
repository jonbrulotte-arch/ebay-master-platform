import httpx

from app.config import settings
from app.exceptions import AliExpressAPIError


class AliExpressClient:
    """AliExpress API client stub — to be implemented in Phase 5."""

    def __init__(self):
        self.app_key = settings.aliexpress_app_key
        self.app_secret = settings.aliexpress_app_secret
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    async def search_products(self, query: str, page: int = 1) -> dict:
        raise NotImplementedError("AliExpress product search — Phase 5")

    async def get_product_detail(self, product_id: str) -> dict:
        raise NotImplementedError("AliExpress product detail — Phase 5")

    async def place_order(self, product_id: str, quantity: int, shipping_address: dict) -> dict:
        raise NotImplementedError("AliExpress order placement — Phase 5")

    async def get_order_tracking(self, order_id: str) -> dict:
        raise NotImplementedError("AliExpress tracking — Phase 5")
