import json
import tempfile
import unittest
from pathlib import Path
from local_historical_backtest import run_archive_directory

class LocalHistoricalBacktestTests(unittest.TestCase):
    def test_empty_directory_is_not_reported_as_no_profitable_opportunities(self):
        with tempfile.TemporaryDirectory() as d:
            r=run_archive_directory(d,str(Path(d)/"output"))
            self.assertEqual(r["status"],"INSUFFICIENT_ARCHIVED_DATA")
            self.assertEqual(r["captured_snapshots"],0)
    def test_offline_capture_replayed_without_api(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            archive={"source_type":"archived_public_orderbook_observations",
                     "research_only":True,"trade_allowed":False,"market_rules_verified":False,
                     "captures":[{"captured_at":"2026-10-28T00:00:00Z","rows":[],"opposing_token_map":{}}]}
            (root/"capture.json").write_text(json.dumps(archive))
            r=run_archive_directory(root,root/"output")
            self.assertEqual(r["captured_snapshots"],1)
            self.assertEqual(r["positive_modeled_sightings"],0)
            self.assertTrue((root/"output"/"local_backtest_results.json").exists())
            self.assertFalse(r["historical_execution_verified"])
if __name__=="__main__":
    unittest.main()
