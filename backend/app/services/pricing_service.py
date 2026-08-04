from decimal import ROUND_HALF_UP, Decimal
from typing import Any

INF = Decimal("99999999")

FEE_TIERS: dict[str, dict[str, list[tuple[Decimal, Decimal]]]] = {
    "starter": {
        "Most Categories": [
            (Decimal("7500"), Decimal("0.1360")),
            (INF, Decimal("0.0235")),
        ],
        "Books, Magazines, Movies & TV, Music": [
            (Decimal("7500"), Decimal("0.1530")),
            (INF, Decimal("0.0235")),
        ],
        "Coins & Paper Money (Excl. Bullion)": [
            (Decimal("7500"), Decimal("0.1325")),
            (INF, Decimal("0.0235")),
        ],
        "Coins & Paper Money > Bullion": [
            (Decimal("7500"), Decimal("0.1360")),
            (INF, Decimal("0.0700")),
        ],
        "Select Collectibles & Toys": [
            (Decimal("7500"), Decimal("0.1325")),
            (INF, Decimal("0.0235")),
        ],
        "Musical Instruments > Guitars & Basses": [
            (Decimal("7500"), Decimal("0.0670")),
            (INF, Decimal("0.0235")),
        ],
        "Jewelry & Watches (Excl. Watches)": [
            (Decimal("5000"), Decimal("0.1500")),
            (INF, Decimal("0.0900")),
        ],
        "Jewelry & Watches > Watches, Parts & Accs": [
            (Decimal("1000"), Decimal("0.1500")),
            (Decimal("7500"), Decimal("0.0650")),
            (INF, Decimal("0.0300")),
        ],
        "NFTs": [
            (INF, Decimal("0.0500")),
        ],
        "Business & Industrial > Heavy Equipment": [
            (Decimal("15000"), Decimal("0.0300")),
            (INF, Decimal("0.0050")),
        ],
        "Clothing, Shoes & Accs > Athletic Shoes": [
            (Decimal("150"), Decimal("0.1360")),
            (INF, Decimal("0.0800")),
        ],
        "Clothing, Shoes & Accs > Handbags": [
            (Decimal("2000"), Decimal("0.1500")),
            (INF, Decimal("0.0900")),
        ],
    },
    "basic_plus": {
        "All Other Categories": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Antiques, Art, Baby, Crafts, Dolls, etc.": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Books, Magazines, Movies & TV, Music": [
            (Decimal("2500"), Decimal("0.1530")),
            (INF, Decimal("0.0235")),
        ],
        "Business & Industrial (Most)": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Business & Industrial > Heavy Equipment": [
            (Decimal("15000"), Decimal("0.0250")),
            (INF, Decimal("0.0050")),
        ],
        "Cameras & Photo (Most)": [
            (Decimal("2500"), Decimal("0.0935")),
            (INF, Decimal("0.0235")),
        ],
        "Cell Phones & Accs (Most)": [
            (Decimal("2500"), Decimal("0.0935")),
            (INF, Decimal("0.0235")),
        ],
        "Clothing, Shoes & Accs (Most)": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Clothing, Shoes & Accs > Handbags": [
            (Decimal("2000"), Decimal("0.1300")),
            (INF, Decimal("0.0700")),
        ],
        "Clothing, Shoes & Accs > Athletic Shoes": [
            (Decimal("150"), Decimal("0.1270")),
            (INF, Decimal("0.0700")),
        ],
        "Coins & Paper Money (Most)": [
            (Decimal("4000"), Decimal("0.0900")),
            (INF, Decimal("0.0235")),
        ],
        "Coins & Paper Money > Bullion": [
            (Decimal("1500"), Decimal("0.0750")),
            (Decimal("10000"), Decimal("0.0500")),
            (INF, Decimal("0.0450")),
        ],
        "Collectibles (Most)": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Collectibles > Comics & Trading Cards": [
            (Decimal("2500"), Decimal("0.1235")),
            (INF, Decimal("0.0235")),
        ],
        "Computers & Networking (Most)": [
            (Decimal("2500"), Decimal("0.0935")),
            (INF, Decimal("0.0235")),
        ],
        "Computers > Select Hardware & Laptops": [
            (Decimal("2500"), Decimal("0.0735")),
            (INF, Decimal("0.0235")),
        ],
        "Consumer Electronics (Most)": [
            (Decimal("2500"), Decimal("0.0935")),
            (INF, Decimal("0.0235")),
        ],
        "Jewelry & Watches (Most)": [
            (Decimal("5000"), Decimal("0.1300")),
            (INF, Decimal("0.0700")),
        ],
        "Jewelry & Watches > Watches, Parts & Accs": [
            (Decimal("1000"), Decimal("0.1250")),
            (Decimal("5000"), Decimal("0.0400")),
            (INF, Decimal("0.0300")),
        ],
        "eBay Motors > Parts & Accs (Most)": [
            (Decimal("1000"), Decimal("0.1150")),
            (INF, Decimal("0.0235")),
        ],
        "eBay Motors > Tires": [
            (Decimal("1000"), Decimal("0.0950")),
            (INF, Decimal("0.0235")),
        ],
        "Music > Vinyl Records": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Musical Instruments & Gear (Most)": [
            (Decimal("2500"), Decimal("0.1035")),
            (INF, Decimal("0.0235")),
        ],
        "Musical Instruments > Guitars & Basses": [
            (Decimal("2500"), Decimal("0.0670")),
            (INF, Decimal("0.0235")),
        ],
        "NFTs": [
            (INF, Decimal("0.0500")),
        ],
        "Sporting Goods, Toys, Home & Garden": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Sports Mem, Cards & Fan Shop (Most)": [
            (Decimal("2500"), Decimal("0.1270")),
            (INF, Decimal("0.0235")),
        ],
        "Sports Mem > Sports Trading Cards": [
            (Decimal("2500"), Decimal("0.1235")),
            (INF, Decimal("0.0235")),
        ],
        "Stamps": [
            (Decimal("2500"), Decimal("0.0970")),
            (INF, Decimal("0.0235")),
        ],
        "Video Games & Consoles > Consoles": [
            (Decimal("2500"), Decimal("0.0735")),
            (INF, Decimal("0.0235")),
        ],
    },
}

NO_PER_ORDER_FEE_OVER: dict[str, Decimal] = {
    "Clothing, Shoes & Accs > Athletic Shoes": Decimal("150"),
}

ALL_CATEGORIES: list[str] = sorted(
    set(list(FEE_TIERS["starter"].keys()) + list(FEE_TIERS["basic_plus"].keys()))
    - {"Most Categories", "All Other Categories"}
) + ["All Other Categories"]


def _calculate_tiered_fee(amount: Decimal, tiers: list[tuple[Decimal, Decimal]]) -> Decimal:
    fee = Decimal("0")
    prev_threshold = Decimal("0")
    for threshold, rate in tiers:
        if amount <= prev_threshold:
            break
        chunk = min(amount, threshold) - prev_threshold
        fee += chunk * rate
        prev_threshold = threshold
    return fee


def _get_tiers(
    store_level: str, category_name: str
) -> tuple[list[tuple[Decimal, Decimal]], Decimal | None]:
    store_group = "starter" if store_level in ("none", "starter") else "basic_plus"
    tiers_map = FEE_TIERS[store_group]
    tiers = tiers_map.get(category_name)
    if tiers is None:
        fallback = "Most Categories" if store_group == "starter" else "All Other Categories"
        tiers = tiers_map[fallback]
    no_per_order_fee_over = NO_PER_ORDER_FEE_OVER.get(category_name)
    return tiers, no_per_order_fee_over


def calculate_fees(
    *,
    sold_price: Decimal,
    item_cost: Decimal,
    actual_shipping_cost: Decimal,
    store_level: str = "basic",
    category_name: str = "All Other Categories",
    shipping_charge_to_buyer: Decimal = Decimal("0"),
    seller_discount_pct: Decimal = Decimal("0"),
    promoted_rate: Decimal = Decimal("0"),
    sales_tax_rate: Decimal = Decimal("0"),
    is_top_rated_seller: bool = False,
) -> dict[str, Any]:
    sold_price = Decimal(str(sold_price))
    item_cost = Decimal(str(item_cost))
    actual_shipping_cost = Decimal(str(actual_shipping_cost))
    shipping_charge_to_buyer = Decimal(str(shipping_charge_to_buyer))
    seller_discount_pct = Decimal(str(seller_discount_pct))
    promoted_rate = Decimal(str(promoted_rate))
    sales_tax_rate = Decimal(str(sales_tax_rate))

    seller_discount_amount = sold_price * seller_discount_pct / Decimal("100")
    effective_sold_price = sold_price - seller_discount_amount

    pre_tax_total = effective_sold_price + shipping_charge_to_buyer
    sales_tax_amount = pre_tax_total * sales_tax_rate / Decimal("100")
    total_sale = pre_tax_total + sales_tax_amount

    tiers, no_per_order_fee_over = _get_tiers(store_level, category_name)
    fee_amount = _calculate_tiered_fee(total_sale, tiers)

    if is_top_rated_seller:
        fee_amount *= Decimal("0.90")

    if no_per_order_fee_over is not None and pre_tax_total > no_per_order_fee_over:
        per_order_fee = Decimal("0")
    elif pre_tax_total > Decimal("10"):
        per_order_fee = Decimal("0.40")
    else:
        per_order_fee = Decimal("0.30")

    final_value_fee = (fee_amount + per_order_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    promoted_fee = (total_sale * promoted_rate / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_fees = final_value_fee + promoted_fee

    payout = pre_tax_total - total_fees
    net_profit = payout - item_cost - actual_shipping_cost

    profit_margin_pct = (
        (net_profit / pre_tax_total * Decimal("100")) if pre_tax_total > 0 else Decimal("0")
    )
    roi_pct = (net_profit / item_cost * Decimal("100")) if item_cost > 0 else Decimal("0")

    q2 = Decimal("0.01")
    return {
        "sold_price": sold_price.quantize(q2),
        "seller_discount_amount": seller_discount_amount.quantize(q2),
        "effective_sold_price": effective_sold_price.quantize(q2),
        "shipping_charge_to_buyer": shipping_charge_to_buyer.quantize(q2),
        "pre_tax_total": pre_tax_total.quantize(q2),
        "sales_tax_amount": sales_tax_amount.quantize(q2),
        "total_sale": total_sale.quantize(q2),
        "final_value_fee": final_value_fee,
        "promoted_fee": promoted_fee,
        "total_fees": total_fees.quantize(q2),
        "payout": payout.quantize(q2),
        "item_cost": item_cost.quantize(q2),
        "actual_shipping_cost": actual_shipping_cost.quantize(q2),
        "net_profit": net_profit.quantize(q2),
        "profit_margin_pct": profit_margin_pct.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        "roi_pct": roi_pct.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
    }


def compute_price_for_target_margin(
    *,
    item_cost: Decimal,
    actual_shipping_cost: Decimal,
    target_margin_pct: Decimal,
    store_level: str = "basic",
    category_name: str = "All Other Categories",
    shipping_charge_to_buyer: Decimal = Decimal("0"),
    seller_discount_pct: Decimal = Decimal("0"),
    promoted_rate: Decimal = Decimal("0"),
    sales_tax_rate: Decimal = Decimal("0"),
    is_top_rated_seller: bool = False,
) -> Decimal:
    lo = Decimal("0.01")
    hi = Decimal("9999.99")
    for _ in range(50):
        mid = (lo + hi) / 2
        result = calculate_fees(
            sold_price=mid,
            item_cost=item_cost,
            actual_shipping_cost=actual_shipping_cost,
            store_level=store_level,
            category_name=category_name,
            shipping_charge_to_buyer=shipping_charge_to_buyer,
            seller_discount_pct=seller_discount_pct,
            promoted_rate=promoted_rate,
            sales_tax_rate=sales_tax_rate,
            is_top_rated_seller=is_top_rated_seller,
        )
        if result["profit_margin_pct"] < target_margin_pct:
            lo = mid
        else:
            hi = mid
    return hi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


DEFAULT_USER_SETTINGS: dict[str, Any] = {
    "ebay_store_level": "basic",
    "is_top_rated_seller": False,
    "default_promoted_rate": 0.0,
    "default_sales_tax_rate": 0.0,
    "default_fee_category": "All Other Categories",
}


def get_default_user_settings() -> dict[str, Any]:
    return dict(DEFAULT_USER_SETTINGS)


def merge_user_settings(user_settings: dict | None) -> dict[str, Any]:
    merged = get_default_user_settings()
    if user_settings:
        for key in DEFAULT_USER_SETTINGS:
            if key in user_settings:
                merged[key] = user_settings[key]
    return merged
