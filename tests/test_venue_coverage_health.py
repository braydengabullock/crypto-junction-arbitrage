import json
import tempfile
import unittest
from pathlib import Path
from venue_coverage_health import inspect


class VenueCoverageTests(unittest.TestCase):
    def test_detects_missing_polymarket_venue(self):
        with tempfile.TemporaryDirectory() as root:
            doc = {"source_type": "archived_public_orderbook_observations",
                   "captures": [{"rows": [{"observations": [{"venue": "kalshi"}]}]}]}
            Path(root, "capture.json").write_text(json.dumps(doc))
            report = inspect(root)
            self.assertFalse(report["healthy"])
            self.assertEqual(report["venue_row_counts"]["polymarket"], 0)
            self.assertEqual(report["status"], "VENUE_COVERAGE_MISSING")

    def test_counts_both_venues(self):
        with tempfile.TemporaryDirectory() as root:
            doc = {"source_type": "archived_public_orderbook_observations",
                   "captures": [{"rows": [{"observations": [
                       {"venue": "kalshi"}, {"venue": "polymarket"}]}]}]}
            Path(root, "capture.json").write_text(json.dumps(doc))
            self.assertTrue(inspect(root)["healthy"])


if __name__ == "__main__":
    unittest.main()
