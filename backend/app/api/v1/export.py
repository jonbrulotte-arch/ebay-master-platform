import csv
import io
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])

_CANCELLED = "CANCELLED"


def _date_range(from_date: date | None, to_date: date | None) -> tuple[datetime, datetime]:
    tz = timezone.utc
    to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=tz) if to_date else datetime.now(tz)
    from_dt = datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0, tzinfo=tz) if from_date else to_dt - timedelta(days=30)
    return from_dt, to_dt


@router.get("/orders")
async def export_orders(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)

    rows = (
        await db.execute(
            text("""
                SELECT
                    o.ebay_order_id,
                    o.buyer_username,
                    o.paid_at,
                    o.order_status,
                    o.payment_status,
                    o.total_amount,
                    o.subtotal,
                    o.shipping_cost,
                    o.tax_amount,
                    o.shipping_carrier,
                    o.tracking_number,
                    COALESCE(SUM(pr.gross_profit), 0)      AS net_profit,
                    COALESCE(AVG(pr.profit_margin_pct), 0) AS margin_pct
                FROM orders o
                LEFT JOIN order_line_items oli ON oli.order_id = o.id
                LEFT JOIN profitability_records pr
                    ON pr.order_line_item_id = oli.id AND pr.record_type = 'ACTUAL'
                WHERE o.user_id = :uid
                  AND o.paid_at >= :from_dt
                  AND o.paid_at <= :to_dt
                GROUP BY o.id
                ORDER BY o.paid_at DESC
            """),
            {"uid": str(current_user.id), "from_dt": from_dt, "to_dt": to_dt},
        )
    ).mappings().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "eBay Order ID", "Buyer Username", "Order Date", "Order Status",
        "Payment Status", "Total Amount", "Subtotal", "Shipping Cost",
        "Tax Amount", "Carrier", "Tracking Number", "Net Profit", "Margin %",
    ])
    for r in rows:
        writer.writerow([
            r["ebay_order_id"],
            r["buyer_username"] or "",
            r["paid_at"].isoformat() if r["paid_at"] else "",
            r["order_status"],
            r["payment_status"],
            f"{float(r['total_amount']):.2f}",
            f"{float(r['subtotal']):.2f}",
            f"{float(r['shipping_cost'] or 0):.2f}",
            f"{float(r['tax_amount'] or 0):.2f}",
            r["shipping_carrier"] or "",
            r["tracking_number"] or "",
            f"{float(r['net_profit']):.2f}",
            f"{float(r['margin_pct']):.2f}",
        ])

    buf.seek(0)
    filename = f"orders_{from_dt.date()}_{to_dt.date()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/profitability")
async def export_profitability(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt, to_dt = _date_range(from_date, to_date)

    rows = (
        await db.execute(
            text("""
                SELECT
                    pr.calculated_at,
                    p.title                                  AS product_title,
                    p.sku,
                    pr.sale_price,
                    pr.cost_of_goods,
                    pr.shipping_cost_from_supplier,
                    pr.ebay_final_value_fee,
                    pr.ebay_promoted_listing_fee,
                    pr.ebay_international_fee,
                    (
                        pr.ebay_final_value_fee +
                        pr.ebay_promoted_listing_fee +
                        pr.ebay_international_fee
                    )                                        AS total_fees,
                    pr.gross_profit,
                    pr.profit_margin_pct,
                    pr.roi_pct
                FROM profitability_records pr
                JOIN products p ON p.id = pr.product_id
                WHERE p.user_id = :uid
                  AND pr.record_type = 'ACTUAL'
                  AND pr.calculated_at >= :from_dt
                  AND pr.calculated_at <= :to_dt
                ORDER BY pr.calculated_at DESC
            """),
            {"uid": str(current_user.id), "from_dt": from_dt, "to_dt": to_dt},
        )
    ).mappings().all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Date", "Product Title", "SKU", "Sale Price", "COGS",
        "Supplier Shipping", "FVF", "Promoted Fee", "International Fee",
        "Total Fees", "Net Profit", "Margin %", "ROI %",
    ])
    for r in rows:
        writer.writerow([
            r["calculated_at"].isoformat() if r["calculated_at"] else "",
            r["product_title"],
            r["sku"] or "",
            f"{float(r['sale_price']):.2f}",
            f"{float(r['cost_of_goods']):.2f}",
            f"{float(r['shipping_cost_from_supplier'] or 0):.2f}",
            f"{float(r['ebay_final_value_fee'] or 0):.2f}",
            f"{float(r['ebay_promoted_listing_fee'] or 0):.2f}",
            f"{float(r['ebay_international_fee'] or 0):.2f}",
            f"{float(r['total_fees'] or 0):.2f}",
            f"{float(r['gross_profit']):.2f}",
            f"{float(r['profit_margin_pct']):.4f}",
            f"{float(r['roi_pct']):.4f}",
        ])

    buf.seek(0)
    filename = f"profitability_{from_dt.date()}_{to_dt.date()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
