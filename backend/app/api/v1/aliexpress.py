import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import AliExpressAPIError, NotFoundError
from app.models.order import Order
from app.models.product_supplier import ProductSupplier
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.aliexpress import (
    AliExpressImportRequest,
    AliExpressImportResponse,
    AliExpressSearchResponse,
    CurrencyRateResponse,
    ForwardOrderRequest,
    ForwardOrderResponse,
    SupplierPriceCheckRequest,
    SupplierPriceCheckResponse,
    SupplierPriceCheckResult,
    TrackingSyncResponse,
)
from app.services import aliexpress_service

router = APIRouter(prefix="/aliexpress", tags=["aliexpress"])


@router.get("/search", response_model=AliExpressSearchResponse)
async def search_products(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    current_user: User = Depends(get_current_user),
):
    try:
        return await aliexpress_service.search_products(
            query=query, page=page, page_size=page_size,
            min_price=min_price, max_price=max_price,
        )
    except AliExpressAPIError as exc:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return await aliexpress_service.get_product_detail(product_id)
    except AliExpressAPIError as exc:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post("/import", response_model=AliExpressImportResponse, status_code=201)
async def import_product(
    body: AliExpressImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await aliexpress_service.import_product(
        data=body.model_dump(),
        user_id=current_user.id,
        db=db,
    )


@router.post("/orders/{order_id}/forward", response_model=ForwardOrderResponse)
async def forward_order(
    order_id: uuid.UUID,
    body: ForwardOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    try:
        ae_order_id = await aliexpress_service.forward_order_to_aliexpress(
            order=order,
            db=db,
            sku_id=body.sku_id,
            logistics_service=body.logistics_service,
        )
    except AliExpressAPIError as exc:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    await db.commit()
    return ForwardOrderResponse(
        order_id=order_id,
        aliexpress_order_id=ae_order_id,
        status="PLACED",
    )


@router.post("/supplier-prices/check", response_model=SupplierPriceCheckResponse)
async def check_supplier_prices(
    body: SupplierPriceCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results: list[SupplierPriceCheckResult] = []
    for ps_id in body.product_supplier_ids:
        ps_result = await db.execute(
            select(ProductSupplier)
            .join(Supplier, Supplier.id == ProductSupplier.supplier_id)
            .where(
                ProductSupplier.id == ps_id,
                Supplier.user_id == current_user.id,
            )
        )
        ps = ps_result.scalar_one_or_none()
        if not ps:
            continue
        result = await aliexpress_service.check_supplier_price(
            product_supplier=ps,
            db=db,
            notify_user_id=current_user.id,
        )
        results.append(result)

    await db.commit()
    changed = sum(1 for r in results if r.changed)
    return SupplierPriceCheckResponse(checked=len(results), changed=changed, results=results)


@router.post("/orders/{order_id}/sync-tracking", response_model=TrackingSyncResponse)
async def sync_order_tracking(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")

    tracking = await aliexpress_service.sync_tracking_for_order(order, db)
    await db.commit()

    synced = 1 if tracking else 0
    return TrackingSyncResponse(
        synced=synced,
        failed=0,
        details=[tracking] if tracking else [],
    )


@router.get("/currency", response_model=CurrencyRateResponse)
async def get_currency_rate(
    safety_margin_pct: float = Query(2.0, ge=0, le=20),
    current_user: User = Depends(get_current_user),
):
    info = aliexpress_service.get_currency_info(safety_margin_pct)
    return CurrencyRateResponse(**info)
