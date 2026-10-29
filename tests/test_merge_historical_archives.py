import unittest
from merge_historical_archives import merge

def archive(ts,rule=False):
    return {"source_type":"archived_public_orderbook_observations","research_only":True,
            "trade_allowed":False,"market_rules_verified":rule,
            "captures":[{"captured_at":ts,"rows":[],"opposing_token_map":{}}]}

class ArchiveMergeTests(unittest.TestCase):
    def test_deduplicates_and_reports_distinct_days(self):
        a=archive("2026-10-27T12:00:00Z")
        b=archive("2026-10-27T12:00:00+00:00")
        c=archive("2026-10-28T12:00:00Z")
        result=merge([a,b,c])
        self.assertEqual(result["capture_count"],2)
        self.assertEqual(result["distinct_utc_dates_observed"],2)
        self.assertEqual(result["rejections"][0]["reason"],"DUPLICATE_CAPTURE_TIME")
        self.assertFalse(result["trade_allowed"])
    def test_rejects_fake_historical_provenance(self):
        result=merge([{"source_type":"synthetic","research_only":True,"captures":[]},archive("2026-10-28T12:00:00Z",rule=True)])
        self.assertEqual(result["capture_count"],0)
        self.assertEqual(len(result["rejections"]),2)
    def test_rejects_missing_timezone(self):
        result=merge([archive("2026-10-28T12:00:00")])
        self.assertEqual(result["capture_count"],0)
        self.assertEqual(result["rejections"][0]["reason"],"INVALID_CAPTURE")

if __name__=="__main__":
    unittest.main()
