import json
import unittest
from pathlib import Path

from po_to_menu_cost.extractor import SchemaError, extract_with_llm, extract_with_rules

DATA = Path(__file__).resolve().parent.parent / "data"


class RuleExtractorTest(unittest.TestCase):
    def test_parses_every_line_of_a_text_po(self):
        text = (DATA / "sample_po.txt").read_text(encoding="utf-8")
        lines = extract_with_rules(text)
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0].sku, "TOM-001")
        self.assertAlmostEqual(lines[0].qty, 5000)
        self.assertEqual(lines[0].unit, "g")

    def test_empty_text_returns_no_lines(self):
        self.assertEqual(extract_with_rules(""), [])


class LlmExtractorTest(unittest.TestCase):
    def _payload(self):
        return [
            {
                "po_id": "PO-3001",
                "date": "2026-10-05",
                "supplier": "Distribuidora Central",
                "sku": "TOM-001",
                "description": "Tomate",
                "qty": 5,
                "unit": "kg",
                "unit_price": 2.10,
            }
        ]

    def test_accepts_valid_model_output(self):
        lines = extract_with_llm("ignored", lambda prompt: json.dumps(self._payload()))
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].sku, "TOM-001")

    def test_rejects_missing_field(self):
        payload = self._payload()
        del payload[0]["unit_price"]
        with self.assertRaises(SchemaError):
            extract_with_llm("ignored", lambda prompt: json.dumps(payload))

    def test_rejects_invalid_json(self):
        with self.assertRaises(SchemaError):
            extract_with_llm("ignored", lambda prompt: "not json")

    def test_rejects_non_numeric_quantity(self):
        payload = self._payload()
        payload[0]["qty"] = "about five"
        with self.assertRaises(SchemaError):
            extract_with_llm("ignored", lambda prompt: json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
