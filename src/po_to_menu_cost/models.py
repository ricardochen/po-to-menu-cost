"""Domain objects. Kept deliberately small and immutable."""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class POLine:
    po_id: str
    date: date
    supplier: str
    sku: str
    description: str
    qty: float
    unit: str
    unit_price: float  # per the stated unit


@dataclass(frozen=True)
class RecipeLine:
    menu_item: str
    sku: str
    qty: float
    unit: str


@dataclass(frozen=True)
class MenuItem:
    name: str
    sale_price: float


@dataclass
class CostBreakdown:
    menu_item: str
    cost: float
    sale_price: float
    missing_skus: list[str] = field(default_factory=list)

    @property
    def margin(self) -> float:
        return round(self.sale_price - self.cost, 2)

    @property
    def margin_pct(self) -> float:
        if self.sale_price <= 0:
            return 0.0
        return round((self.sale_price - self.cost) / self.sale_price * 100, 1)


@dataclass(frozen=True)
class PriceChange:
    sku: str
    previous: float  # per base unit (kg or L)
    current: float
    pct: float
