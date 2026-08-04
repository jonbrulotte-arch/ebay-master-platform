"""Service layer for eBay credential management and client instantiation."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ebay import auth as ebay_auth
from app.integrations.ebay.client import EbayClient
from app.models.ebay_credential import EbayCredential
from app.utils.encryption import decrypt_token, encrypt_token


async def get_active_credential(
    db: AsyncSession, user_id: uuid.UUID, marketplace: str = "EBAY_US"
) -> EbayCredential | None:
    result = await db.execute(
        select(EbayCredential).where(
            EbayCredential.user_id == user_id,
            EbayCredential.marketplace == marketplace,
            EbayCredential.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def get_ebay_client(
    db: AsyncSession, user_id: uuid.UUID, marketplace: str = "EBAY_US"
) -> EbayClient:
    cred = await get_active_credential(db, user_id, marketplace)
    if not cred:
        raise ValueError(f"No active eBay credentials for user {user_id}")

    # Auto-refresh if token expires within 5 minutes
    if cred.token_expires_at and cred.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
        cred = await refresh_credential(db, cred)

    access_token = decrypt_token(cred.access_token)
    return EbayClient(access_token)


async def refresh_credential(db: AsyncSession, cred: EbayCredential) -> EbayCredential:
    refresh_token = decrypt_token(cred.refresh_token)
    token_data = await ebay_auth.refresh_access_token(refresh_token)

    cred.access_token = encrypt_token(token_data["access_token"])
    if "refresh_token" in token_data:
        cred.refresh_token = encrypt_token(token_data["refresh_token"])
    expires_in = token_data.get("expires_in", 7200)
    cred.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    await db.commit()
    await db.refresh(cred)
    return cred


async def save_credential(
    db: AsyncSession,
    user_id: uuid.UUID,
    token_data: dict,
    marketplace: str = "EBAY_US",
) -> EbayCredential:
    # Deactivate any existing credentials for this marketplace
    result = await db.execute(
        select(EbayCredential).where(
            EbayCredential.user_id == user_id,
            EbayCredential.marketplace == marketplace,
        )
    )
    existing = result.scalars().all()
    for cred in existing:
        cred.is_active = False

    expires_in = token_data.get("expires_in", 7200)
    new_cred = EbayCredential(
        user_id=user_id,
        marketplace=marketplace,
        access_token=encrypt_token(token_data["access_token"]),
        refresh_token=encrypt_token(token_data["refresh_token"]),
        token_expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        scopes=token_data.get("scope", "").split(),
        is_active=True,
    )
    db.add(new_cred)
    await db.commit()
    await db.refresh(new_cred)
    return new_cred


async def refresh_all_expiring_tokens(db: AsyncSession) -> dict:
    """Refresh tokens expiring in under 1 hour. Used by the maintenance Celery task."""
    soon = datetime.now(timezone.utc) + timedelta(hours=1)
    result = await db.execute(
        select(EbayCredential).where(
            EbayCredential.is_active == True,
            EbayCredential.token_expires_at < soon,
        )
    )
    creds = result.scalars().all()

    refreshed = 0
    failed = 0
    for cred in creds:
        try:
            await refresh_credential(db, cred)
            refreshed += 1
        except Exception:
            failed += 1

    return {"refreshed": refreshed, "failed": failed}
