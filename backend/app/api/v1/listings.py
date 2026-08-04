import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.listing import Listing
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.listing import ListingCreate, ListingResponse, ListingUpdate

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=PaginatedResponse[ListingResponse])
async def list_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    marketplace: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Listing).where(Listing.user_id == current_user.id)
    if status:
        query = query.where(Listing.status == status)
    if marketplace:
        query = query.where(Listing.marketplace == marketplace)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Listing.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    listings = result.scalars().all()

    return PaginatedResponse(
        items=[ListingResponse.model_validate(l) for l in listings],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(
    listing_in: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = Listing(user_id=current_user.id, **listing_in.model_dump())
    db.add(listing)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundError("Listing not found")
    return listing


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: uuid.UUID,
    listing_in: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundError("Listing not found")

    for field, value in listing_in.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)
    await db.flush()
    await db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id, Listing.user_id == current_user.id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundError("Listing not found")
    await db.delete(listing)
