"""eBay Inventory API client — manages inventory items and offers (listings)."""
from typing import Any

from app.integrations.ebay.client import EbayClient

INVENTORY_API = "/sell/inventory/v1"
FULFILLMENT_API_URL = "/sell/account/v1"


class EbayInventoryAPI:
    def __init__(self, client: EbayClient):
        self.client = client

    # --- Inventory Items ---

    async def create_or_replace_inventory_item(self, sku: str, payload: dict) -> dict:
        return await self.client.put(
            f"{INVENTORY_API}/inventory_item/{sku}", json=payload
        )

    async def get_inventory_item(self, sku: str) -> dict:
        return await self.client.get(f"{INVENTORY_API}/inventory_item/{sku}")

    async def get_inventory_items(self, limit: int = 25, offset: int = 0) -> dict:
        return await self.client.get(
            f"{INVENTORY_API}/inventory_item",
            params={"limit": limit, "offset": offset},
        )

    async def delete_inventory_item(self, sku: str) -> dict:
        return await self.client.delete(f"{INVENTORY_API}/inventory_item/{sku}")

    async def bulk_create_or_replace_inventory_item(self, requests: list[dict]) -> dict:
        return await self.client.post(
            f"{INVENTORY_API}/bulk_create_or_replace_inventory_item",
            json={"requests": requests},
        )

    # --- Offers ---

    async def create_offer(self, payload: dict) -> dict:
        return await self.client.post(f"{INVENTORY_API}/offer", json=payload)

    async def get_offer(self, offer_id: str) -> dict:
        return await self.client.get(f"{INVENTORY_API}/offer/{offer_id}")

    async def get_offers(self, sku: str) -> dict:
        return await self.client.get(
            f"{INVENTORY_API}/offer", params={"sku": sku, "marketplace_id": "EBAY_US"}
        )

    async def update_offer(self, offer_id: str, payload: dict) -> dict:
        return await self.client.put(f"{INVENTORY_API}/offer/{offer_id}", json=payload)

    async def delete_offer(self, offer_id: str) -> dict:
        return await self.client.delete(f"{INVENTORY_API}/offer/{offer_id}")

    async def publish_offer(self, offer_id: str) -> dict:
        return await self.client.post(
            f"{INVENTORY_API}/offer/{offer_id}/publish", json={}
        )

    async def withdraw_offer(self, offer_id: str) -> dict:
        return await self.client.post(
            f"{INVENTORY_API}/offer/{offer_id}/withdraw", json={}
        )

    async def bulk_create_offer(self, requests: list[dict]) -> dict:
        return await self.client.post(
            f"{INVENTORY_API}/bulk_create_offer",
            json={"requests": requests},
        )

    async def bulk_publish_offer(self, offer_ids: list[str]) -> dict:
        return await self.client.post(
            f"{INVENTORY_API}/bulk_publish_offer",
            json={"requests": [{"offerId": oid} for oid in offer_ids]},
        )

    # --- Helpers ---

    def build_inventory_item_payload(
        self,
        product: Any,
        supplier_cost: float,
        quantity: int,
        condition: str = "USED_EXCELLENT",
    ) -> dict:
        payload: dict = {
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": quantity,
                }
            },
            "condition": condition,
            "product": {
                "title": product.title,
                "description": product.description or product.title,
                "aspects": product.item_specifics or {},
                "imageUrls": [],
            },
        }
        if product.brand:
            payload["product"]["brand"] = product.brand
        if product.mpn:
            payload["product"]["mpn"] = product.mpn
        if product.upc:
            payload["product"]["upc"] = [product.upc]
        if product.ean:
            payload["product"]["ean"] = [product.ean]
        if product.isbn:
            payload["product"]["isbn"] = [product.isbn]
        return payload

    def build_offer_payload(
        self,
        sku: str,
        price: float,
        category_id: str,
        shipping_policy_id: str,
        return_policy_id: str,
        payment_policy_id: str,
        quantity: int = 1,
        description_html: str | None = None,
        promoted_listing_rate: float | None = None,
        listing_duration: str = "GTC",
    ) -> dict:
        payload: dict = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingDuration": listing_duration,
            "availableQuantity": quantity,
            "categoryId": category_id,
            "pricingSummary": {
                "price": {"value": str(price), "currency": "USD"}
            },
            "listingPolicies": {
                "fulfillmentPolicyId": shipping_policy_id,
                "returnPolicyId": return_policy_id,
                "paymentPolicyId": payment_policy_id,
            },
        }
        if description_html:
            payload["description"] = description_html
        if promoted_listing_rate is not None:
            payload["listingPolicies"]["ebayPlusIfEligible"] = False
        return payload
