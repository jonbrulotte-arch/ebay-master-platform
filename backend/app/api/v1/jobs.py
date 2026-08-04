from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job_history import JobHistory
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.job import JobHistoryResponse, ManualTriggerRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedResponse[JobHistoryResponse])
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    job_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JobHistory).where(
        (JobHistory.user_id == current_user.id) | (JobHistory.user_id == None)  # noqa: E711
    )
    if job_type:
        query = query.where(JobHistory.job_type == job_type)
    if status:
        query = query.where(JobHistory.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(JobHistory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=[JobHistoryResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/trigger")
async def trigger_job(
    body: ManualTriggerRequest,
    current_user: User = Depends(get_current_user),
):
    """Manually enqueue a Celery task by job_type name."""
    from app.tasks.celery_app import celery_app

    ALLOWED_TASKS = {
        "sync_orders": "app.tasks.ebay_sync.sync_orders",
        "sync_listings": "app.tasks.ebay_sync.sync_listings",
        "refresh_tokens": "app.tasks.maintenance.refresh_tokens",
        "reprice_check": "app.tasks.repricing.reprice_check",
        "check_low_stock": "app.tasks.inventory_tasks.check_low_stock",
        "check_supplier_prices": "app.tasks.supplier_monitoring.check_supplier_prices",
        "sync_tracking": "app.tasks.aliexpress_sync.sync_tracking",
        "daily_profitability_recalc": "app.tasks.profitability.recalculate_all",
        "generate_daily_summary": "app.tasks.maintenance.generate_daily_summary",
    }

    task_name = ALLOWED_TASKS.get(body.job_type)
    if not task_name:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown job type: {body.job_type}")

    result = celery_app.send_task(task_name)
    return {"task_id": result.id, "job_type": body.job_type, "status": "queued"}
