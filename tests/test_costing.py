import unittest
from pathlib import Path

from po_to_menu_cost.costing import cost_menu_item, latest_prices, price_changes
from po_to_menu_cost.parser import load_menu_items, load_purchase_orders, load_recipes

DATA = Path(__file__).resolve().parent.parent / "data"


class CostingTest(unittest.TestCase):
    def setUp(self):
        self.orders = load_purchase_orders(DATA / "purchase_orders.csv")
        self.recipes = load_recipes(DATA / "recipes.csv")
        self.items = {item.name: item for item in load_menu_items(DATA / "menu_items.csv")}
        self.prices = latest_prices(self.orders)

    def test_latest_price_wins(self):
        self.assertAlmostEqual(self.prices["TOM-001"], 2.10)

    def test_cost_uses_grain_recipe_units(self):
        breakdown = cost_menu_item(self.items["Ensalada Cesar"], self.recipes, self.prices)
        self.assertAlmostEqual(breakdown.cost, 1.52, places=2)

    def test_margin_percentage(self):
        breakdown = cost_menu_item(self.items["Ensalada Cesar"], self.recipes, self.prices)
        self.assertAlmostEqual(breakdown.margin_pct, 87.3, places=1)

    def test_missing_price_is_reported_not_crashed(self):
        breakdown = cost_menu_item(self.items["Pasta primavera"], self.recipes, {"TOM-001": 2.10})
        self.assertIn("CHS-005", breakdown.missing_skus)
        self.assertAlmostEqual(breakdown.cost, 0.21, places=2)

    def test_price_changes_are_sorted_by_magnitude(self):
        changes = price_changes(self.orders)
        self.assertEqual(changes[0].sku, "TOM-001")
        self.assertAlmostEqual(changes[0].pct, 13.5, places=1)
        self.assertEqual(len(changes), 4)


if __name__ == "__main__":
    unittest.main()
