import hashlib
import json
import time
from typing import Any

import httpx

from app.config import settings
from app.exceptions import AliExpressAPIError

_BASE_URL = "https://api.taobao.com/router/rest"


class AliExpressClient:
    """AliExpress Open Platform API client (MD5 signature scheme)."""

    def __init__(self):
        self.app_key = settings.aliexpress_app_key
        self.app_secret = settings.aliexpress_app_secret
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _sign(self, params: dict[str, str]) -> str:
        sorted_pairs = sorted(params.items())
        body = "".join(f"{k}{v}" for k, v in sorted_pairs)
        raw = self.app_secret + body + self.app_secret
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    def _base_params(self, method: str) -> dict[str, str]:
        return {
            "method": method,
            "app_key": self.app_key,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "md5",
        }

    async def _call(self, method: str, extra: dict[str, Any]) -> dict:
        if not self.app_key or not self.app_secret:
            raise AliExpressAPIError(
                "AliExpress API keys not configured — set ALIEXPRESS_APP_KEY and ALIEXPRESS_APP_SECRET"
            )
        params: dict[str, str] = {
            **self._base_params(method),
            **{k: str(v) for k, v in extra.items()},
        }
        params["sign"] = self._sign({k: v for k, v in params.items() if k != "sign"})
        resp = await self._client.post(_BASE_URL, data=params)
        resp.raise_for_status()
        data = resp.json()
        if "error_response" in data:
            err = data["error_response"]
            raise AliExpressAPIError(
                err.get("msg", "Unknown error"),
                is_transient=err.get("code") in ("27", "50"),  # rate limit / system error
            )
        return data

    # ── Product search ────────────────────────────────────────────────────────

    async def search_products(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        min_price: float | None = None,
        max_price: float | None = None,
        sort: str = "SALE_PRICE_ASC",
    ) -> dict:
        extra: dict[str, Any] = {
            "keywords": query,
            "page_no": page,
            "page_size": min(page_size, 50),
            "currency": "USD",
            "sort": sort,
            "target_currency": "USD",
            "target_language": "EN",
            "tracking_id": self.app_key,
        }
        if min_price is not None:
            extra["min_sale_price"] = int(min_price * 100)  # API expects cents
        if max_price is not None:
            extra["max_sale_price"] = int(max_price * 100)
        return await self._call("aliexpress.affiliate.product.query", extra)

    async def get_product_detail(self, product_id: str) -> dict:
        return await self._call("aliexpress.affiliate.product.detail.query", {
            "product_id": product_id,
            "target_currency": "USD",
            "target_language": "EN",
            "tracking_id": self.app_key,
        })

    # ── Dropship orders ───────────────────────────────────────────────────────

    async def place_dropship_order(
        self,
        product_id: str,
        sku_id: str,
        quantity: int,
        shipping_address: dict,
        logistics_service: str = "YANWEN_REGULAR_AIRMAIL",
    ) -> dict:
        product_items = json.dumps([{
            "product_id": product_id,
            "product_count": quantity,
            "sku_id": sku_id,
        }])
        address = {
            "contact_person": shipping_address.get("name", ""),
            "mobile_no": shipping_address.get("phone", ""),
            "detail_address": shipping_address.get("address_line1", ""),
            "city": shipping_address.get("city", ""),
            "province": shipping_address.get("state", ""),
            "zip": shipping_address.get("postal_code", ""),
            "country": shipping_address.get("country_code", "US"),
        }
        return await self._call("aliexpress.ds.order.create.request.upload", {
            "product_items": product_items,
            "logistics_address": json.dumps(address),
        })

    async def get_order_tracking(self, ae_order_id: str) -> dict:
        return await self._call("aliexpress.ds.order.tracking.list.query", {
            "order_id": ae_order_id,
        })

    async def get_order_detail(self, ae_order_id: str) -> dict:
        return await self._call("aliexpress.ds.order.detail.query", {
            "order_id": ae_order_id,
        })
