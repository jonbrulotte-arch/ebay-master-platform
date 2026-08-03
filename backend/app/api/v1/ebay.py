"""eBay integration endpoints: OAuth flow, policies, categories, account health."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.ebay import auth as ebay_auth
from app.integrations.ebay.account_api import EbayAccountAPI
from app.models.user import User
from app.services.ebay_service import (
    get_active_credential,
    get_ebay_client,
    save_credential,
)

router = APIRouter(prefix="/ebay", tags=["ebay"])


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class ConnectionStatus(BaseModel):
    connected: bool
    marketplace: str
    expires_at: str | None = None
    scopes: list[str] = []


# --- OAuth Flow ---

@router.get("/connect")
async def get_connect_url(
    current_user: User = Depends(get_current_user),
):
    """Return the eBay OAuth consent URL to redirect the user to."""
    url = ebay_auth.get_consent_url(state=str(current_user.id))
    return {"url": url}


@router.post("/callback")
async def oauth_callback(
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exchange authorization code for tokens and save to DB."""
    try:
        token_data = await ebay_auth.exchange_code_for_token(body.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}")

    await save_credential(db, current_user.id, token_data)
    return {"status": "connected", "message": "eBay account connected successfully"}


@router.get("/status", response_model=ConnectionStatus)
async def connection_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the user has active eBay credentials."""
    cred = await get_active_credential(db, current_user.id)
    if not cred:
        return ConnectionStatus(connected=False, marketplace="EBAY_US")
    return ConnectionStatus(
        connected=True,
        marketplace=cred.marketplace,
        expires_at=cred.token_expires_at.isoformat() if cred.token_expires_at else None,
        scopes=cred.scopes or [],
    )


@router.delete("/disconnect")
async def disconnect(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate stored eBay credentials."""
    from sqlalchemy import select
    from app.models.ebay_credential import EbayCredential

    result = await db.execute(
        select(EbayCredential).where(
            EbayCredential.user_id == current_user.id,
            EbayCredential.is_active == True,
        )
    )
    creds = result.scalars().all()
    for cred in creds:
        cred.is_active = False
    await db.commit()
    return {"status": "disconnected"}


# --- Seller Policies ---

@router.get("/policies/fulfillment")
async def get_fulfillment_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = await _require_client(db, current_user.id)
    try:
        return await EbayAccountAPI(client).get_fulfillment_policies()
    finally:
        await client.close()


@router.get("/policies/return")
async def get_return_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = await _require_client(db, current_user.id)
    try:
        return await EbayAccountAPI(client).get_return_policies()
    finally:
        await client.close()


@router.get("/policies/payment")
async def get_payment_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = await _require_client(db, current_user.id)
    try:
        return await EbayAccountAPI(client).get_payment_policies()
    finally:
        await client.close()


# --- Account Health / Privileges ---

@router.get("/account/privileges")
async def get_privileges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = await _require_client(db, current_user.id)
    try:
        return await EbayAccountAPI(client).get_privileges()
    finally:
        await client.close()


# --- Listings Actions (publish / end) ---

@router.post("/listings/{listing_id}/publish")
async def publish_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.listing_service import publish_listing as svc_publish
    from app.exceptions import EbayAPIError

    try:
        listing = await svc_publish(db, current_user.id, listing_id)
        return {"status": "published", "ebay_item_id": listing.ebay_item_id}
    except EbayAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/listings/{listing_id}/end")
async def end_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.listing_service import end_listing as svc_end
    from app.exceptions import EbayAPIError

    try:
        listing = await svc_end(db, current_user.id, listing_id)
        return {"status": listing.status}
    except EbayAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# --- Manual Sync Triggers ---

@router.post("/sync/orders")
async def trigger_order_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger order sync for the current user."""
    from app.services.order_service import sync_orders_for_user

    result = await sync_orders_for_user(db, current_user.id)
    return result


@router.post("/sync/listings")
async def trigger_listing_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger listing status sync for the current user."""
    from app.services.listing_service import sync_listings_for_user

    result = await sync_listings_for_user(db, current_user.id)
    return result


# --- Helpers ---

async def _require_client(db, user_id):
    try:
        return await get_ebay_client(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
