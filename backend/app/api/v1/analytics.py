from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    FeeBreakdownResponse,
    RevenueDataPoint,
    SummaryResponse,
    TopProductResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

_CANCELLED = "CANCELLED"


def _date_range(from_date: date | None, to_date: date | None) -> tuple[datetime, datetime]:
    tz = timezone.utc
    if to_date is None:
        to_dt = datetime.now(tz)
    else:
        to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=tz)
    if from_date is None:
        from_dt = to_dt - timedelta(days=30)
    else:
        from_dt = datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0, tzinfo=tz)
    return from_dt, to_dt


async def _fetch_summary(
    db: AsyncSession, user_id: str, from_dt: datetime, to_dt: datetime
) -> SummaryResponse:
    row = (
        await db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT o.id)                                     AS order_count,
                    COALESCE(SUM(o.total_amount), 0)                         AS gross_revenue,
                    COALESCE(SUM(pr.gross_profit), 0)                        AS net_profit,
                    COALESCE(AVG(pr.profit_margin_pct), 0)                   AS avg_margin_pct,
                    COALESCE(AVG(pr.roi_pct), 0)                             AS avg_roi_pct,
                    COALESCE(SUM(oli.quantity), 0)                           AS units_sold,
                    COALESCE(SUM(
                        COALESCE(oli.ebay_final_value_fee, 0) +
                        COALESCE(oli.ebay_promoted_listing_fee, 0) +
                        COALESCE(oli.ebay_international_fee, 0)
                    ), 0)                                                    AS total_fees
                FROM orders o
                LEFT JOIN order_line_items oli ON oli.order_id = o.id
                LEFT JOIN profitability_records pr
                    ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                WHERE o.user_id = :uid
                  AND o.order_status != :cancelled
                  AND o.paid_at >= :from_dt
                  AND o.paid_at <= :to_dt
            """),
            {"uid": str(user_id), "cancelled": _CANCELLED, "from_dt": from_dt, "to_dt": to_dt},
        )
    ).mappings().one()

    return SummaryResponse(
        order_count=int(row["order_count"] or 0),
        gross_revenue=float(row["gross_revenue"] or 0),
        net_profit=float(row["net_profit"] or 0),
        avg_margin_pct=float(row["avg_margin_pct"] or 0),
        avg_roi_pct=float(row["avg_roi_pct"] or 0),
        units_sold=int(row["units_sold"] or 0),
        total_fees=float(row["total_fees"] or 0),
    )


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    include_previous: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)
    result = await _fetch_summary(db, current_user.id, from_dt, to_dt)

    if include_previous:
        duration = to_dt - from_dt
        prev_to = from_dt - timedelta(seconds=1)
        prev_from = prev_to - duration
        result.previous_period = await _fetch_summary(db, current_user.id, prev_from, prev_to)

    return result


@router.get("/revenue-over-time", response_model=list[RevenueDataPoint])
async def get_revenue_over_time(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)

    rows = (
        await db.execute(
            text(f"""
                SELECT
                    DATE_TRUNC('{granularity}', o.paid_at) AT TIME ZONE 'UTC' AS period,
                    COALESCE(SUM(o.total_amount), 0)                           AS revenue,
                    COALESCE(SUM(pr.gross_profit), 0)                          AS profit,
                    COUNT(DISTINCT o.id)                                        AS orders,
                    COALESCE(SUM(oli.quantity), 0)                             AS units
                FROM orders o
                LEFT JOIN order_line_items oli ON oli.order_id = o.id
                LEFT JOIN profitability_records pr
                    ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                WHERE o.user_id = :uid
                  AND o.order_status != :cancelled
                  AND o.paid_at >= :from_dt
                  AND o.paid_at <= :to_dt
                GROUP BY DATE_TRUNC('{granularity}', o.paid_at)
                ORDER BY period
            """),
            {"uid": str(current_user.id), "cancelled": _CANCELLED, "from_dt": from_dt, "to_dt": to_dt},
        )
    ).mappings().all()

    return [
        RevenueDataPoint(
            period=row["period"].isoformat() if hasattr(row["period"], "isoformat") else str(row["period"]),
            revenue=float(row["revenue"] or 0),
            profit=float(row["profit"] or 0),
            orders=int(row["orders"] or 0),
            units=int(row["units"] or 0),
        )
        for row in rows
    ]


@router.get("/top-products", response_model=list[TopProductResponse])
async def get_top_products(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    sort_by: str = Query("revenue", pattern="^(revenue|profit|units)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)

    sort_col = {"revenue": "revenue", "profit": "profit", "units": "units_sold"}[sort_by]

    rows = (
        await db.execute(
            text(f"""
                SELECT
                    p.id::text                             AS product_id,
                    p.title                                AS title,
                    p.sku                                  AS sku,
                    COALESCE(SUM(oli.quantity), 0)         AS units_sold,
                    COALESCE(SUM(oli.total_price), 0)      AS revenue,
                    COALESCE(SUM(pr.gross_profit), 0)      AS profit,
                    COALESCE(AVG(pr.profit_margin_pct), 0) AS avg_margin_pct
                FROM order_line_items oli
                JOIN orders o     ON o.id = oli.order_id
                JOIN products p   ON p.id = oli.product_id
                LEFT JOIN profitability_records pr
                    ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                WHERE o.user_id = :uid
                  AND o.order_status != :cancelled
                  AND o.paid_at >= :from_dt
                  AND o.paid_at <= :to_dt
                GROUP BY p.id, p.title, p.sku
                ORDER BY {sort_col} DESC
                LIMIT :lim
            """),
            {
                "uid": str(current_user.id),
                "cancelled": _CANCELLED,
                "from_dt": from_dt,
                "to_dt": to_dt,
                "lim": limit,
            },
        )
    ).mappings().all()

    return [
        TopProductResponse(
            product_id=row["product_id"],
            title=row["title"],
            sku=row["sku"],
            units_sold=int(row["units_sold"] or 0),
            revenue=float(row["revenue"] or 0),
            profit=float(row["profit"] or 0),
            avg_margin_pct=float(row["avg_margin_pct"] or 0),
        )
        for row in rows
    ]


@router.get("/fee-breakdown", response_model=FeeBreakdownResponse)
async def get_fee_breakdown(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)

    row = (
        await db.execute(
            text("""
                SELECT
                    COALESCE(SUM(oli.ebay_final_value_fee), 0)       AS final_value_fees,
                    COALESCE(SUM(oli.ebay_promoted_listing_fee), 0)  AS promoted_fees,
                    COALESCE(SUM(oli.ebay_international_fee), 0)     AS international_fees,
                    COALESCE(SUM(pr.cost_of_goods), 0)               AS cogs,
                    COALESCE(SUM(pr.shipping_cost_from_supplier), 0) AS shipping_costs,
                    COALESCE(SUM(pr.gross_profit), 0)                AS net_profit
                FROM order_line_items oli
                JOIN orders o ON o.id = oli.order_id
                LEFT JOIN profitability_records pr
                    ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                WHERE o.user_id = :uid
                  AND o.order_status != :cancelled
                  AND o.paid_at >= :from_dt
                  AND o.paid_at <= :to_dt
            """),
            {"uid": str(current_user.id), "cancelled": _CANCELLED, "from_dt": from_dt, "to_dt": to_dt},
        )
    ).mappings().one()

    return FeeBreakdownResponse(
        final_value_fees=float(row["final_value_fees"] or 0),
        promoted_fees=float(row["promoted_fees"] or 0),
        international_fees=float(row["international_fees"] or 0),
        cogs=float(row["cogs"] or 0),
        shipping_costs=float(row["shipping_costs"] or 0),
        net_profit=float(row["net_profit"] or 0),
    )
