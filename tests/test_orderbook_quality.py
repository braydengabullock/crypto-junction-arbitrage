import unittest
from orderbook_quality import summarize

T="2026-10-28T12:00:00Z"
def row(t=T):
    return {"kalshi_ticker":"K","polymarket_id":"P","errors":[],
            "observations":[
              {"venue":"kalshi","request_started_at":T,"observed_at":T,
               "book":{"orderbook_fp":{"no_dollars":[["0.60","5"]],"yes_dollars":[]}}},
              {"venue":"polymarket","request_started_at":t,"observed_at":t,
               "book":{"asks":[{"price":"0.40","size":"5"}]}}]}
class QualityTests(unittest.TestCase):
    def test_complete_but_nonactionable(self):
        r=summarize({"research_only":True,"rows":[row()]})
        self.assertEqual(r["rows_with_displayed_depth_on_both_venues"],1)
        self.assertEqual(r["rows_with_synchronized_observations"],1)
        self.assertEqual(r["verified_opportunities"],0)
        self.assertFalse(r["backtest_ready"])
    def test_stale_capture(self):
        r=summarize({"research_only":True,"rows":[row("2026-10-28T12:01:00Z")]})
        self.assertEqual(r["rows_with_synchronized_observations"],0)
    def test_long_request_window_is_not_synchronized(self):
        data=row()
        data["observations"][1]["request_started_at"]="2026-10-28T11:59:00Z"
        r=summarize({"research_only":True,"rows":[data]})
        self.assertEqual(r["rows_with_synchronized_observations"],0)
    def test_unusable(self):
        r=summarize({"research_only":True,"rows":[{"errors":["API unavailable"],"observations":[]}]})
        self.assertEqual(r["request_errors"],1)
        self.assertEqual(r["rows_with_kalshi_and_polymarket_books"],0)
    def test_reject_nonresearch_data(self):
        with self.assertRaises(ValueError): summarize({"rows":[]})
if __name__=="__main__":
    unittest.main()
