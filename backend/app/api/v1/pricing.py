import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.fee_schedule import FeeSchedule
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
)

router = APIRouter(prefix="/pricing", tags=["pricing"])


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


@router.post("/fee-calculator", response_model=FeeCalculationResponse)
async def calculate_fees(
    req: FeeCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fvf_pct = Decimal("13.25")
    pp_pct = Decimal("2.35")
    pp_fixed = Decimal("0.25")
    intl_pct = Decimal("1.65")

    if req.category_id:
        result = await db.execute(
            select(FeeSchedule).where(
                FeeSchedule.category_id == req.category_id,
                FeeSchedule.marketplace == "EBAY_US",
            ).order_by(FeeSchedule.effective_from.desc()).limit(1)
        )
        fee_schedule = result.scalar_one_or_none()
        if fee_schedule:
            fvf_pct = Decimal(str(fee_schedule.final_value_fee_pct))
            pp_pct = Decimal(str(fee_schedule.payment_processing_pct))
            pp_fixed = Decimal(str(fee_schedule.payment_processing_fixed))
            intl_pct = Decimal(str(fee_schedule.international_fee_pct))

    sale = Decimal(str(req.sale_price))
    cogs = Decimal(str(req.cost_of_goods))
    supplier_ship = Decimal(str(req.supplier_shipping_cost))
    ship = Decimal(str(req.shipping_cost))

    final_value_fee = sale * fvf_pct / 100
    payment_fee = sale * pp_pct / 100 + pp_fixed
    promoted_fee = (
        sale * Decimal(str(req.promoted_listing_rate)) / 100
        if req.promoted_listing_rate
        else Decimal("0")
    )
    international_fee = sale * intl_pct / 100 if req.is_international else Decimal("0")

    total_fees = final_value_fee + payment_fee + promoted_fee + international_fee
    total_costs = cogs + supplier_ship + total_fees + ship
    gross_profit = sale - total_costs
    margin = (gross_profit / sale * 100) if sale > 0 else Decimal("0")
    roi = (gross_profit / cogs * 100) if cogs > 0 else Decimal("0")

    return FeeCalculationResponse(
        sale_price=float(sale),
        cost_of_goods=float(cogs),
        supplier_shipping_cost=float(supplier_ship),
        ebay_final_value_fee=float(final_value_fee.quantize(Decimal("0.01"))),
        ebay_payment_processing_fee=float(payment_fee.quantize(Decimal("0.01"))),
        ebay_promoted_listing_fee=float(promoted_fee.quantize(Decimal("0.01"))),
        ebay_international_fee=float(international_fee.quantize(Decimal("0.01"))),
        shipping_cost=float(ship),
        total_fees=float(total_fees.quantize(Decimal("0.01"))),
        total_costs=float(total_costs.quantize(Decimal("0.01"))),
        gross_profit=float(gross_profit.quantize(Decimal("0.01"))),
        profit_margin_pct=float(margin.quantize(Decimal("0.01"))),
        roi_pct=float(roi.quantize(Decimal("0.01"))),
    )
