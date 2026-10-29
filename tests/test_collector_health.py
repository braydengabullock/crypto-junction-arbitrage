import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from collector_health import inspect

NOW=datetime(2026,10,28,12,3,tzinfo=timezone.utc)
class CollectorHealthTests(unittest.TestCase):
    def test_recent_capture_is_usable_but_not_trade_verified(self):
        with tempfile.TemporaryDirectory() as d:
            a={"source_type":"archived_public_orderbook_observations","research_only":True,
               "trade_allowed":False,"captures":[{"captured_at":"2026-10-28T12:00:00Z",
                 "rows":[{"kalshi_ticker":"K"}]}]}
            Path(d,"a.json").write_text(json.dumps(a))
            r=inspect(d,as_of=NOW)
            self.assertTrue(r["ready"])
            self.assertFalse(r["trade_allowed"])
    def test_empty_or_stale_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(inspect(d,as_of=NOW)["ready"])
            a={"source_type":"archived_public_orderbook_observations","research_only":True,
               "trade_allowed":False,"captures":[{"captured_at":"2026-10-28T11:00:00Z","rows":[]}]}
            Path(d,"a.json").write_text(json.dumps(a))
            self.assertFalse(inspect(d,as_of=NOW)["ready"])
if __name__=="__main__": unittest.main()
