# PO → menu cost

Turn supplier purchase orders into **cost and margin per dish**, with a flag when a supplier price moves.

```
Item                      Cost    Price    Margin
Ensalada Cesar            1.52    12.00     87.3%
Pollo a la plancha        1.50    14.50     89.7%
Pasta primavera           0.70    11.00     93.6%

Supplier price changes
TOM-001       1.85 ->    2.10   +13.5%
CHK-003       5.60 ->    5.20   -7.1%
OIL-004       9.20 ->    9.80   +6.5%
LET-002       2.40 ->    2.55   +6.2%
```

## Why this exists

I owned and ran a restaurant. Menu costing was a weekly job done by hand: read the supplier invoices, find what each ingredient costs now, multiply by the recipe, compare against the price on the menu. It takes an hour, it's wrong whenever a price changes, and nobody does it during a busy week — which is exactly when margins move.

This is the small version of that job, extracted from the system I built to run the restaurant's purchasing and costing.

## What it does

1. **Loads** purchase orders, recipes and menu prices from CSV.
2. **Normalises units** before any arithmetic — recipes are written in grams, invoices in kilograms.
3. **Prices each dish** from the most recent purchase of each ingredient.
4. **Reports margin** per dish and **flags supplier price moves** above a threshold (default 5%).
5. **Extracts purchase order lines from free text**, with schema validation before the data reaches the costing code.

## Design decisions

**Units are normalised first, and there is a test for it.** Mixing `150 g` with a `2.10 / kg` price is the most common way this calculation goes quietly wrong — a dish costs 1,000× too much and nobody notices. `normalise_qty` and `price_per_base_unit` make the conversion explicit and tested.

**Validation runs before costing.** The LLM path does not write into the costing code directly. It returns JSON, `validate_payload` checks every required field and type, and a malformed line raises `SchemaError` rather than costing a dish at zero. An LLM that invents a plausible line with a missing price is a worse failure than one that returns nothing.

**Missing prices are reported, not swallowed.** If an ingredient has no purchase history, the dish cost is computed from what is known and the SKU is listed under `missing_skus`. Silently treating it as zero would make the margin look better than it is.

**The pricing policy is stated in one place.** "Most recent purchase" is a deliberate simplification, not an accident — see *Not production-ready* below.

**The rule-based extractor is the test oracle.** `extract_with_rules` parses a fixed format with regex and no model, so the LLM path can be tested against deterministic output.

## Quickstart

No runtime dependencies — standard library only, Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

po-to-menu-cost --data data
po-to-menu-cost --extract data/sample_po.txt
```

Without installing:

```bash
PYTHONPATH=src python -m po_to_menu_cost.cli --data data
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

20 tests covering unit conversion, price-per-base-unit scaling, margin maths, missing SKUs, price-change ordering, and the extraction schema (valid JSON, missing field, non-numeric quantity, invalid JSON).

## Using a model for extraction

`extract_with_llm` accepts any callable that maps a prompt to a JSON string, so the model is a dependency you inject rather than one baked in:

```python
from po_to_menu_cost.extractor import extract_with_llm

lines = extract_with_llm(text, llm=my_llm_call)
```

Everything below that line — normalisation, costing, margins — is model-free and tested.

## What is mocked

- **The data.** Suppliers, SKUs and prices are fictional.
- **The recipes.** Simplified quantities, not a real kitchen's.
- **The pricing policy.** Latest purchase, not weighted average or FIFO.
- **No database, no auth, no UI.** This is the calculation core, not a product.

## What I would do next

1. **Weighted-average costing** instead of latest price, with a per-ingredient policy switch.
2. **Yield and waste factors** — a case of tomatoes does not yield a case of sliced tomatoes.
3. **An eval set for extraction**: 30 real invoices with expected line items, scored on field-level accuracy, run in CI.
4. **Price alerts as events**, so a 13% move in a key ingredient reaches the person who sets the menu price.
