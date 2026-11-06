import unittest
from pathlib import Path

from po_to_menu_cost.parser import (
    load_menu_items,
    load_purchase_orders,
    load_recipes,
    normalise_qty,
    price_per_base_unit,
)

DATA = Path(__file__).resolve().parent.parent / "data"


class NormaliseQtyTest(unittest.TestCase):
    def test_grams_become_kilograms(self):
        self.assertEqual(normalise_qty(150, "g"), (0.15, "kg"))

    def test_millilitres_become_litres(self):
        self.assertEqual(normalise_qty(250, "ml"), (0.25, "L"))

    def test_kilograms_pass_through(self):
        self.assertEqual(normalise_qty(2, "kg"), (2.0, "kg"))

    def test_unknown_unit_is_rejected(self):
        with self.assertRaises(ValueError):
            normalise_qty(1, "bunch")


class PricePerBaseUnitTest(unittest.TestCase):
    def test_price_per_kilogram_is_unchanged(self):
        self.assertEqual(price_per_base_unit(2.10, "kg"), 2.10)

    def test_price_per_gram_is_scaled_to_kilogram(self):
        self.assertAlmostEqual(price_per_base_unit(0.0021, "g"), 2.10, places=6)


class LoadersTest(unittest.TestCase):
    def test_loads_purchase_orders(self):
        self.assertEqual(len(load_purchase_orders(DATA / "purchase_orders.csv")), 10)

    def test_loads_recipes(self):
        self.assertEqual(len(load_recipes(DATA / "recipes.csv")), 8)

    def test_loads_menu_items(self):
        self.assertEqual(len(load_menu_items(DATA / "menu_items.csv")), 3)


if __name__ == "__main__":
    unittest.main()
