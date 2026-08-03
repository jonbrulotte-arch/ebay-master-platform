"""eBay Account API — seller policies, privileges, fulfillment/return/payment policies."""
from app.integrations.ebay.client import EbayClient

ACCOUNT_API = "/sell/account/v1"


class EbayAccountAPI:
    def __init__(self, client: EbayClient):
        self.client = client

    async def get_fulfillment_policies(self, marketplace_id: str = "EBAY_US") -> dict:
        return await self.client.get(
            f"{ACCOUNT_API}/fulfillment_policy",
            params={"marketplace_id": marketplace_id},
        )

    async def get_return_policies(self, marketplace_id: str = "EBAY_US") -> dict:
        return await self.client.get(
            f"{ACCOUNT_API}/return_policy",
            params={"marketplace_id": marketplace_id},
        )

    async def get_payment_policies(self, marketplace_id: str = "EBAY_US") -> dict:
        return await self.client.get(
            f"{ACCOUNT_API}/payment_policy",
            params={"marketplace_id": marketplace_id},
        )

    async def get_privileges(self) -> dict:
        return await self.client.get(f"{ACCOUNT_API}/privilege")

    async def get_subscription(self) -> dict:
        return await self.client.get(f"{ACCOUNT_API}/subscription")
