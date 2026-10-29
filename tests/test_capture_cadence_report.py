import unittest
from datetime import datetime, timezone
from capture_cadence_report import evaluate

def doc(*times):
    return {"captures":[{"captured_at":x,"rows":[{"kalshi_ticker":"K"}]} for x in times]}

FIXED=datetime(2026,10,28,0,45,tzinfo=timezone.utc)
class CadenceTests(unittest.TestCase):
    def test_empty_archive_never_claims_complete(self):
        r=evaluate(doc(),as_of=FIXED)
        self.assertEqual(r["capture_count_in_window"],0)
        self.assertFalse(r["complete_24_hour_monitoring_verified"])
    def test_regular_interval(self):
        r=evaluate(doc("2026-10-28T00:00:00Z","2026-10-28T00:15:00Z","2026-10-28T00:30:00Z"),as_of=FIXED)
        self.assertEqual(r["estimated_missing_captures_within_observed_span"],0)
        self.assertEqual(r["market_rows_observed_in_window"],3)
        self.assertFalse(r["complete_24_hour_monitoring_verified"])
    def test_gap_is_not_hidden(self):
        r=evaluate(doc("2026-10-28T00:00:00Z","2026-10-28T00:45:00Z"),as_of=FIXED)
        self.assertEqual(r["estimated_missing_captures_within_observed_span"],2)
        self.assertEqual(r["gaps_exceeding_1_5x_target"],1)
    def test_stale_observation_visible(self):
        r=evaluate(doc("2026-10-28T00:00:00Z"),as_of=FIXED)
        self.assertTrue(r["latest_capture_is_stale"])
        self.assertEqual(r["minutes_since_last_observation"],45)
    def test_filters_older_days(self):
        r=evaluate(doc("2026-10-26T00:00:00Z","2026-10-28T00:00:00Z"),as_of=FIXED)
        self.assertEqual(r["capture_count_in_window"],1)
if __name__=="__main__":
    unittest.main()
