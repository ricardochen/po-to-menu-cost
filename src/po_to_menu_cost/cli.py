"""Command line entry point: cost the menu, or parse a text purchase order."""

import argparse
from pathlib import Path

from .costing import cost_menu_item, latest_prices, price_changes
from .extractor import extract_with_rules
from .parser import load_menu_items, load_purchase_orders, load_recipes


def _cost_report(data: Path, threshold: float) -> int:
    orders = load_purchase_orders(data / "purchase_orders.csv")
    recipes = load_recipes(data / "recipes.csv")
    items = load_menu_items(data / "menu_items.csv")
    prices = latest_prices(orders)

    print("Menu costing")
    print("-" * 54)
    print(f"{'Item':<22}{'Cost':>8}{'Price':>9}{'Margin':>10}")
    for item in items:
        breakdown = cost_menu_item(item, recipes, prices)
        print(
            f"{breakdown.menu_item:<22}{breakdown.cost:>8.2f}"
            f"{breakdown.sale_price:>9.2f}{breakdown.margin_pct:>9.1f}%"
        )
        if breakdown.missing_skus:
            print(f"  ! missing prices for: {', '.join(breakdown.missing_skus)}")

    changes = price_changes(orders, threshold_pct=threshold)
    if changes:
        print("\nSupplier price changes")
        print("-" * 54)
        for change in changes:
            print(
                f"{change.sku:<10}{change.previous:>8.2f} -> {change.current:>7.2f}"
                f"   {change.pct:+.1f}%"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data", help="directory with the CSV inputs")
    parser.add_argument("--extract", help="path to a text purchase order to parse")
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="minimum price change to report, in percent",
    )
    args = parser.parse_args(argv)

    if args.extract:
        lines = extract_with_rules(Path(args.extract).read_text(encoding="utf-8"))
        print(f"{len(lines)} lines extracted")
        for line in lines:
            print(
                f"{line.sku:<10}{line.description:<24}{line.qty:>8.2f} "
                f"{line.unit:<3}{line.unit_price:>8.2f}"
            )
        return 0

    return _cost_report(Path(args.data), args.threshold)


if __name__ == "__main__":
    raise SystemExit(main())
