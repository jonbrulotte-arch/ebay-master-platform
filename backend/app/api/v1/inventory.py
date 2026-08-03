import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import InventoryAdjust, InventoryResponse, InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=PaginatedResponse[InventoryResponse])
async def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Inventory)
        .join(Product)
        .where(Product.user_id == current_user.id)
    )
    if low_stock_only:
        query = query.where(
            Inventory.reorder_point.isnot(None),
            Inventory.quantity_available <= Inventory.reorder_point,
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[InventoryResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/low-stock", response_model=list[InventoryResponse])
async def low_stock_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Inventory)
        .join(Product)
        .where(
            Product.user_id == current_user.id,
            Inventory.reorder_point.isnot(None),
            Inventory.quantity_available <= Inventory.reorder_point,
        )
    )
    return result.scalars().all()


@router.get("/{product_id}", response_model=InventoryResponse)
async def get_inventory(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Inventory)
        .join(Product)
        .where(Inventory.product_id == product_id, Product.user_id == current_user.id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise NotFoundError("Inventory record not found")
    return inv


@router.patch("/{product_id}", response_model=InventoryResponse)
async def update_inventory(
    product_id: uuid.UUID,
    inv_in: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Inventory)
        .join(Product)
        .where(Inventory.product_id == product_id, Product.user_id == current_user.id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise NotFoundError("Inventory record not found")

    for field, value in inv_in.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    await db.flush()
    await db.refresh(inv)
    return inv


@router.post("/{product_id}/adjust", response_model=InventoryResponse)
async def adjust_inventory(
    product_id: uuid.UUID,
    adjust: InventoryAdjust,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Inventory)
        .join(Product)
        .where(Inventory.product_id == product_id, Product.user_id == current_user.id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise NotFoundError("Inventory record not found")

    inv.quantity_available = max(0, inv.quantity_available + adjust.adjustment)
    await db.flush()
    await db.refresh(inv)
    return inv
