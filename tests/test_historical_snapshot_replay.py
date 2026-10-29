import unittest
from historical_snapshot_replay import replay

def capture(at,price="0.50"):
    return {"captured_at":at,"opposing_token_map":{"K|YES":"123"},
        "rows":[{"kalshi_ticker":"K","observations":[
            {"venue":"kalshi","request_started_at":at,"observed_at":at,
             "book":{"orderbook_fp":{"no_dollars":[["0.65","20"]],"yes_dollars":[]}}},
            {"venue":"polymarket","token_id":"123","request_started_at":at,
             "observed_at":at,"book":{"asks":[{"price":price,"size":"20"}]}}]}]}

class HistoricalReplayTests(unittest.TestCase):
    def test_saved_snapshots_with_small_positive_roi_included(self):
        archive={"source_type":"archived_public_orderbook_observations","captures":[
            capture("2026-09-01T12:00:00Z",price="0.64")]}
        r=replay(archive,poly_rate="0",kalshi_multiplier="0",extra_cost="0")
        self.assertEqual(r["capture_count_accepted"],1)
        self.assertEqual(r["total_positive_candidate_observations"],1)
        self.assertFalse(r["historical_execution_verified"])
        self.assertFalse(r["trade_allowed"])
    def test_repeated_market_sightings_not_counted_as_separate_trades(self):
        archive={"source_type":"archived_public_orderbook_observations","captures":[
            capture("2026-09-01T12:00:00Z",price="0.64"),
            capture("2026-09-01T16:00:00Z",price="0.63")]}
        r=replay(archive,poly_rate="0",kalshi_multiplier="0",extra_cost="0")
        self.assertEqual(r["total_positive_candidate_observations"],2)
        self.assertEqual(r["distinct_positive_market_pairs_observed"],1)
        self.assertEqual(r["independent_profitable_trades_established"],0)
    def test_unknown_provenance_rejected(self):
        with self.assertRaises(ValueError):
            replay({"source_type":"synthetic_fixture","captures":[]})
    def test_missing_mapping_and_duplicates_rejected(self):
        t="2026-09-01T12:00:00Z"
        no_map=capture("2026-09-02T12:00:00Z")
        del no_map["opposing_token_map"]
        archive={"source_type":"archived_public_orderbook_observations","captures":[capture(t),capture(t),no_map]}
        r=replay(archive,poly_rate="0",kalshi_multiplier="0",extra_cost="0")
        self.assertEqual(r["capture_count_accepted"],1)
        self.assertEqual(r["capture_count_rejected"],2)
    def test_no_fake_30_day_coverage(self):
        r=replay({"source_type":"archived_public_orderbook_observations",
                  "captures":[capture("2026-09-01T12:00:00Z")]},
                 poly_rate="0",kalshi_multiplier="0",extra_cost="0")
        self.assertEqual(r["observed_timespan_days"],"0")
if __name__=="__main__":
    unittest.main()
