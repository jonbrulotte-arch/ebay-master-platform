import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.message import Message
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=PaginatedResponse[MessageResponse])
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    is_read: bool | None = None,
    direction: str | None = Query(None, regex="^(INBOUND|OUTBOUND)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Message).where(Message.user_id == current_user.id)
    if is_read is not None:
        query = query.where(Message.is_read == is_read)
    if direction:
        query = query.where(Message.direction == direction)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    messages = result.scalars().all()

    return PaginatedResponse(
        items=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count()).where(
            Message.user_id == current_user.id,
            Message.direction == "INBOUND",
            Message.is_read == False,  # noqa: E712
        )
    )
    return {"count": result.scalar() or 0}


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == current_user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message not found")
    return msg


@router.patch("/{message_id}/read")
async def mark_read(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Message)
        .where(Message.id == message_id, Message.user_id == current_user.id)
        .values(is_read=True)
    )
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Message)
        .where(Message.user_id == current_user.id, Message.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    return {"message": "All messages marked as read"}


@router.post("", response_model=MessageResponse, status_code=201)
async def send_message(
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = Message(
        user_id=current_user.id,
        direction="OUTBOUND",
        **body.model_dump(),
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg
