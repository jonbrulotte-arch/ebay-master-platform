import base64
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.integrations.ebay.client import EBAY_AUTH_BASE

SCOPES = [
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.marketing",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
    "https://api.ebay.com/oauth/api_scope/commerce.taxonomy.readonly",
]


def get_consent_url(state: str = "") -> str:
    scope_str = " ".join(SCOPES)
    return (
        f"{EBAY_AUTH_BASE}/oauth2/authorize"
        f"?client_id={settings.ebay_client_id}"
        f"&redirect_uri={settings.ebay_redirect_uri}"
        f"&response_type=code"
        f"&scope={scope_str}"
        f"&state={state}"
    )


async def exchange_code_for_token(code: str) -> dict:
    credentials = base64.b64encode(
        f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EBAY_AUTH_BASE}/identity/v1/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.ebay_redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> dict:
    credentials = base64.b64encode(
        f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EBAY_AUTH_BASE}/identity/v1/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": " ".join(SCOPES),
            },
        )
        response.raise_for_status()
        return response.json()
