import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.order import Order
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderListResponse, OrderResponse, OrderShipRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=PaginatedResponse[OrderListResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    order_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Order).where(Order.user_id == current_user.id)
    if order_status:
        query = query.where(Order.order_status == order_status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    return PaginatedResponse(
        items=[OrderListResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.line_items))
        .where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")
    return order


@router.post("/{order_id}/ship", response_model=OrderResponse)
async def ship_order(
    order_id: uuid.UUID,
    ship_in: OrderShipRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.line_items))
        .where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    order.shipping_carrier = ship_in.shipping_carrier
    order.tracking_number = ship_in.tracking_number
    order.order_status = "SHIPPED"
    await db.flush()
    await db.refresh(order)
    return order
