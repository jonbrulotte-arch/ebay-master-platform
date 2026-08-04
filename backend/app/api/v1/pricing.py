import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.price_change_log import PriceChangeLog
from app.models.pricing_rule import PricingRule
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.pricing import (
    FeeCalculationRequest,
    FeeCalculationResponse,
    PriceChangeLogResponse,
    PricingRuleCreate,
    PricingRuleResponse,
    PricingRuleUpdate,
    UserSettingsRequest,
    UserSettingsResponse,
)
from app.services.pricing_service import ALL_CATEGORIES, calculate_fees, merge_user_settings

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/categories", response_model=list[str])
async def list_fee_categories(current_user: User = Depends(get_current_user)):
    return ALL_CATEGORIES


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = merge_user_settings(current_user.settings)
    return UserSettingsResponse(**settings)


@router.put("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    req: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = dict(current_user.settings or {})
    updates = req.model_dump(exclude_unset=True)
    existing.update(updates)
    current_user.settings = existing
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    settings = merge_user_settings(current_user.settings)
    return UserSettingsResponse(**settings)


@router.post("/fee-calculator", response_model=FeeCalculationResponse)
async def calculate_fees_endpoint(
    req: FeeCalculationRequest,
    current_user: User = Depends(get_current_user),
):
    result = calculate_fees(
        sold_price=Decimal(str(req.sold_price)),
        item_cost=Decimal(str(req.item_cost)),
        actual_shipping_cost=Decimal(str(req.actual_shipping_cost)),
        store_level=req.store_level,
        category_name=req.category_name,
        shipping_charge_to_buyer=Decimal(str(req.shipping_charge_to_buyer)),
        seller_discount_pct=Decimal(str(req.seller_discount_pct)),
        promoted_rate=Decimal(str(req.promoted_rate)),
        sales_tax_rate=Decimal(str(req.sales_tax_rate)),
        is_top_rated_seller=req.is_top_rated_seller,
    )
    return FeeCalculationResponse(**{k: float(v) for k, v in result.items()})


@router.get("/rules", response_model=list[PricingRuleResponse])
async def list_pricing_rules(
    product_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PricingRule).where(PricingRule.user_id == current_user.id)
    if product_id:
        query = query.where(PricingRule.product_id == product_id)
    if is_active is not None:
        query = query.where(PricingRule.is_active == is_active)

    query = query.order_by(PricingRule.priority.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rules", response_model=PricingRuleResponse, status_code=201)
async def create_pricing_rule(
    rule_in: PricingRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = PricingRule(user_id=current_user.id, **rule_in.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_pricing_rule(
    rule_id: uuid.UUID,
    rule_in: PricingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PricingRule).where(
            PricingRule.id == rule_id, PricingRule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Pricing rule not found")

    for field, value in rule_in.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_pricing_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PricingRule).where(
            PricingRule.id == rule_id, PricingRule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Pricing rule not found")
    await db.delete(rule)


@router.get("/change-log", response_model=PaginatedResponse[PriceChangeLogResponse])
async def list_price_changes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    listing_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PriceChangeLog)
    if listing_id:
        query = query.where(PriceChangeLog.listing_id == listing_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = (
        query.order_by(PriceChangeLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[PriceChangeLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
