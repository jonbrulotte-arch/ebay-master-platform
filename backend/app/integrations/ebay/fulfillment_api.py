"""eBay Fulfillment API client — orders, shipping, tracking."""
from app.integrations.ebay.client import EbayClient

FULFILLMENT_API = "/sell/fulfillment/v1"


class EbayFulfillmentAPI:
    def __init__(self, client: EbayClient):
        self.client = client

    async def get_orders(
        self,
        filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
        order_ids: list[str] | None = None,
    ) -> dict:
        params: dict = {"limit": limit, "offset": offset}
        if filter:
            params["filter"] = filter
        if order_ids:
            params["orderIds"] = ",".join(order_ids)
        return await self.client.get(f"{FULFILLMENT_API}/order", params=params)

    async def get_order(self, order_id: str) -> dict:
        return await self.client.get(f"{FULFILLMENT_API}/order/{order_id}")

    async def get_orders_since(self, since_iso: str) -> list[dict]:
        """Paginate through all orders modified since the given ISO timestamp."""
        results = []
        offset = 0
        limit = 50
        filter_str = f"lastmodifieddate:[{since_iso}]"
        while True:
            page = await self.get_orders(filter=filter_str, limit=limit, offset=offset)
            orders = page.get("orders", [])
            results.extend(orders)
            total = page.get("total", 0)
            offset += limit
            if offset >= total:
                break
        return results

    async def get_shipping_fulfillments(self, order_id: str) -> dict:
        return await self.client.get(
            f"{FULFILLMENT_API}/order/{order_id}/shipping_fulfillment"
        )

    async def create_shipping_fulfillment(
        self, order_id: str, tracking_number: str, carrier: str, line_item_ids: list[str]
    ) -> dict:
        payload = {
            "lineItems": [
                {"lineItemId": lid, "quantity": 1} for lid in line_item_ids
            ],
            "shippedDate": None,
            "shippingCarrierCode": carrier,
            "trackingNumber": tracking_number,
        }
        return await self.client.post(
            f"{FULFILLMENT_API}/order/{order_id}/shipping_fulfillment",
            json=payload,
        )

    async def issue_refund(self, order_id: str, reason_type: str, comment: str = "") -> dict:
        payload = {
            "reasonForRefund": reason_type,
            "comment": comment,
            "refundItems": [],
        }
        return await self.client.post(
            f"{FULFILLMENT_API}/order/{order_id}/issue_refund",
            json=payload,
        )
