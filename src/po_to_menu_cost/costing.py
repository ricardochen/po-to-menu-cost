"""Cost each menu item from the latest supplier prices, and flag price moves."""

from collections import defaultdict

from .models import CostBreakdown, MenuItem, POLine, PriceChange, RecipeLine
from .parser import normalise_qty, price_per_base_unit


def latest_prices(polines: list[POLine]) -> dict[str, float]:
    """Price per base unit for each SKU, using the most recent purchase order."""
    prices: dict[str, float] = {}
    for line in sorted(polines, key=lambda l: (l.date, l.po_id)):
        prices[line.sku] = price_per_base_unit(line.unit_price, line.unit)
    return prices


def cost_menu_item(
    item: MenuItem,
    recipes: list[RecipeLine],
    prices: dict[str, float],
) -> CostBreakdown:
    """Sum recipe quantities at the latest price. Missing SKUs are reported, not hidden."""
    cost = 0.0
    missing: list[str] = []
    for line in recipes:
        if line.menu_item != item.name:
            continue
        qty_base, _ = normalise_qty(line.qty, line.unit)
        price = prices.get(line.sku)
        if price is None:
            missing.append(line.sku)
            continue
        cost += qty_base * price
    return CostBreakdown(
        menu_item=item.name,
        cost=round(cost, 2),
        sale_price=item.sale_price,
        missing_skus=missing,
    )


def price_changes(polines: list[POLine], threshold_pct: float = 5.0) -> list[PriceChange]:
    """Compare the two most recent purchases per SKU, in base-unit terms."""
    by_sku: dict[str, list[POLine]] = defaultdict(list)
    for line in polines:
        by_sku[line.sku].append(line)

    changes: list[PriceChange] = []
    for sku, lines in by_sku.items():
        if len(lines) < 2:
            continue
        lines.sort(key=lambda l: (l.date, l.po_id))
        previous, current = lines[-2], lines[-1]
        prev_price = price_per_base_unit(previous.unit_price, previous.unit)
        curr_price = price_per_base_unit(current.unit_price, current.unit)
        if prev_price == 0:
            continue
        pct = (curr_price - prev_price) / prev_price * 100
        if abs(pct) >= threshold_pct:
            changes.append(
                PriceChange(
                    sku=sku,
                    previous=round(prev_price, 2),
                    current=round(curr_price, 2),
                    pct=round(pct, 1),
                )
            )
    return sorted(changes, key=lambda c: -abs(c.pct))
