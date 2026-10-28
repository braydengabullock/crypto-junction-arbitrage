import copy
import unittest
from depth_fee_screen import screen

class QuoteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data={"rows":[{"kalshi_ticker":"K","observations":[
            {"venue":"kalshi","request_started_at":"2026-10-28T10:00:00+00:00",
             "observed_at":"2026-10-28T10:00:01+00:00",
             "book":{"orderbook_fp":{"no_dollars":[["0.65","100"]],"yes_dollars":[]}}},
            {"venue":"polymarket","token_id":"123",
             "request_started_at":"2026-10-28T10:00:02+00:00",
             "observed_at":"2026-10-28T10:00:03+00:00",
             "book":{"asks":[{"price":"0.50","size":"100"}]}}]}]}
    def run_screen(self,data):
        return screen(data,poly_rate="0.05",kalshi_multiplier="1",
                      extra_cost="0.01",opposing_tokens={"K|YES":"123"})
    def test_fresh_books_have_ten_contract_depth(self):
        q=self.run_screen(self.data)["near_misses"][0]["quote_quality"]
        self.assertTrue(q["both_books_present"])
        self.assertTrue(q["within_20_seconds"])
        self.assertTrue(q["sufficient_depth_for_ten"])
        self.assertEqual(q["max_observation_span_seconds"],3)
    def test_stale_pair_is_not_fresh(self):
        data=copy.deepcopy(self.data)
        data["rows"][0]["observations"][1]["observed_at"]="2026-10-28T10:00:30+00:00"
        q=self.run_screen(data)["near_misses"][0]["quote_quality"]
        self.assertFalse(q["within_20_seconds"])
        self.assertEqual(q["max_observation_span_seconds"],30)
    def test_missing_timestamps_fail_closed(self):
        data=copy.deepcopy(self.data)
        del data["rows"][0]["observations"][1]["observed_at"]
        q=self.run_screen(data)["near_misses"][0]["quote_quality"]
        self.assertFalse(q["within_20_seconds"])
        self.assertIsNone(q["max_observation_span_seconds"])
    def test_insufficient_ten_contract_depth(self):
        data=copy.deepcopy(self.data)
        data["rows"][0]["observations"][1]["book"]["asks"][0]["size"]="5"
        q=self.run_screen(data)["near_misses"][0]["quote_quality"]
        self.assertFalse(q["sufficient_depth_for_ten"])
        self.assertTrue(q["within_20_seconds"])

if __name__=="__main__":
    unittest.main()
