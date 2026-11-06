"""Extract purchase order lines from free text.

Two paths:
- `extract_with_rules`: deterministic regex parser, no model, used as the test oracle.
- `extract_with_llm`: takes any callable that maps a prompt to a JSON string, then
  validates the payload against a schema before it can touch the costing code.

The schema check is the point. An LLM that returns a plausible-looking line with a
missing price must fail loudly, not silently cost a dish at zero.
"""

import json
import re
from datetime import date

from .models import POLine

REQUIRED_FIELDS = {
    "po_id",
    "date",
    "supplier",
    "sku",
    "description",
    "qty",
    "unit",
    "unit_price",
}

_HEADER_RE = re.compile(r"^(?P<po_id>PO-\d+)\s+(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<supplier>.+)$")
_LINE_RE = re.compile(
    r"^(?P<sku>[A-Z]{3}-\d{3})\s+(?P<description>.+?)\s+"
    r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|L|ml|unit)\s+"
    r"(?P<unit_price>\d+(?:\.\d+)?)$"
)


class SchemaError(ValueError):
    """Raised when extracted data cannot be trusted as a purchase order line."""


def validate_payload(payload: object) -> list[POLine]:
    if not isinstance(payload, list):
        raise SchemaError("expected a JSON array of purchase order lines")
    lines: list[POLine] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise SchemaError(f"line {index}: expected an object")
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise SchemaError(f"line {index}: missing {sorted(missing)}")
        try:
            lines.append(
                POLine(
                    po_id=str(row["po_id"]),
                    date=date.fromisoformat(str(row["date"])),
                    supplier=str(row["supplier"]),
                    sku=str(row["sku"]),
                    description=str(row["description"]),
                    qty=float(row["qty"]),
                    unit=str(row["unit"]),
                    unit_price=float(row["unit_price"]),
                )
            )
        except (TypeError, ValueError) as exc:
            raise SchemaError(f"line {index}: {exc}") from exc
    return lines


def extract_with_rules(text: str) -> list[POLine]:
    """Deterministic parser. Used in tests and as the fallback when no model is configured."""
    header: dict[str, str] | None = None
    payload: list[dict[str, object]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        header_match = _HEADER_RE.match(line)
        if header_match:
            header = header_match.groupdict()
            continue
        line_match = _LINE_RE.match(line)
        if line_match and header:
            payload.append({**header, **line_match.groupdict()})
    return validate_payload(payload)


def extract_with_llm(text: str, llm) -> list[POLine]:
    """`llm` is any callable: (prompt) -> JSON string."""
    prompt = (
        "Extract purchase order lines from the text below. "
        "Return only a JSON array; each item must have exactly these fields: "
        f"{sorted(REQUIRED_FIELDS)}. Dates are ISO 8601. Do not invent lines."
        f"\n\n{text}"
    )
    raw = llm(prompt)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"model did not return valid JSON: {exc}") from exc
    return validate_payload(payload)
