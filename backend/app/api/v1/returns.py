import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.order import Order
from app.models.return_ import Return
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.return_ import ReturnResponse, ReturnUpdate

router = APIRouter(prefix="/returns", tags=["returns"])


@router.get("", response_model=PaginatedResponse[ReturnResponse])
async def list_returns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Return)
        .join(Order, Order.id == Return.order_id)
        .where(Order.user_id == current_user.id)
    )
    if status:
        query = query.where(Return.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Return.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    returns = result.scalars().all()

    return PaginatedResponse(
        items=[ReturnResponse.model_validate(r) for r in returns],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{return_id}", response_model=ReturnResponse)
async def get_return(
    return_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Return)
        .join(Order, Order.id == Return.order_id)
        .where(Return.id == return_id, Order.user_id == current_user.id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise NotFoundError("Return not found")
    return ret


@router.patch("/{return_id}", response_model=ReturnResponse)
async def update_return(
    return_id: uuid.UUID,
    body: ReturnUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Return)
        .join(Order, Order.id == Return.order_id)
        .where(Return.id == return_id, Order.user_id == current_user.id)
    )
    ret = result.scalar_one_or_none()
    if not ret:
        raise NotFoundError("Return not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ret, field, value)
    await db.flush()
    await db.refresh(ret)
    return ret
