"""Load and normalise purchase orders, recipes and menu prices.

Units are normalised to a base unit (kg, L or unit) before any arithmetic.
That is the whole point: a recipe in grams and an invoice in kilograms must
never be compared without conversion.
"""

import csv
from datetime import datetime
from pathlib import Path

from .models import MenuItem, POLine, RecipeLine

# unit -> (base unit, factor to multiply a quantity by)
UNITS: dict[str, tuple[str, float]] = {
    "kg": ("kg", 1.0),
    "g": ("kg", 0.001),
    "l": ("L", 1.0),
    "ml": ("L", 0.001),
    "unit": ("unit", 1.0),
}


def normalise_qty(qty: float, unit: str) -> tuple[float, str]:
    """Return (quantity in base unit, base unit)."""
    key = unit.strip().lower()
    if key not in UNITS:
        raise ValueError(f"unsupported unit: {unit!r}")
    base, factor = UNITS[key]
    return qty * factor, base


def price_per_base_unit(unit_price: float, unit: str) -> float:
    """Convert a price quoted per `unit` into a price per base unit."""
    key = unit.strip().lower()
    if key not in UNITS:
        raise ValueError(f"unsupported unit: {unit!r}")
    _, factor = UNITS[key]
    if factor == 0:
        raise ValueError("unit factor cannot be zero")
    return unit_price / factor


def _fail(path: Path, line_no: int, exc: Exception) -> ValueError:
    return ValueError(f"{path}:{line_no}: {exc}")


def load_purchase_orders(path: str | Path) -> list[POLine]:
    path = Path(path)
    rows: list[POLine] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            try:
                rows.append(
                    POLine(
                        po_id=row["po_id"].strip(),
                        date=datetime.strptime(row["date"].strip(), "%Y-%m-%d").date(),
                        supplier=row["supplier"].strip(),
                        sku=row["sku"].strip(),
                        description=row["description"].strip(),
                        qty=float(row["qty"]),
                        unit=row["unit"].strip(),
                        unit_price=float(row["unit_price"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise _fail(path, line_no, exc) from exc
    return rows


def load_recipes(path: str | Path) -> list[RecipeLine]:
    path = Path(path)
    rows: list[RecipeLine] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            try:
                rows.append(
                    RecipeLine(
                        menu_item=row["menu_item"].strip(),
                        sku=row["ingredient_sku"].strip(),
                        qty=float(row["qty"]),
                        unit=row["unit"].strip(),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise _fail(path, line_no, exc) from exc
    return rows


def load_menu_items(path: str | Path) -> list[MenuItem]:
    path = Path(path)
    rows: list[MenuItem] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for line_no, row in enumerate(csv.DictReader(fh), start=2):
            try:
                rows.append(
                    MenuItem(
                        name=row["menu_item"].strip(),
                        sale_price=float(row["sale_price"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise _fail(path, line_no, exc) from exc
    return rows
