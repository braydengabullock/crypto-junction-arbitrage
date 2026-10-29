import unittest
from archive_research_capture import build
from historical_snapshot_replay import replay

class ArchiveCaptureTests(unittest.TestCase):
    def test_real_observation_shape_replays_without_claiming_fills(self):
        t="2026-10-28T20:00:00Z"
        books={"captured_at":t,"rows":[{"kalshi_ticker":"K","observations":[
            {"venue":"kalshi","observed_at":t,"request_started_at":t,
             "book":{"orderbook_fp":{"no_dollars":[["0.65","20"]],"yes_dollars":[]}}},
            {"venue":"polymarket","token_id":"123","observed_at":t,"request_started_at":t,
             "book":{"asks":[{"price":"0.64","size":"20"}]}}],"errors":[]}]}
        mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                 "market_rules_verified":False,"opposing_token_map":{"K|YES":"123"}}
        packaged=build(books,mapping)
        self.assertEqual(packaged["books_with_observations"],1)
        result=replay(packaged,poly_rate="0",kalshi_multiplier="0",extra_cost="0")
        self.assertEqual(result["capture_count_accepted"],1)
        self.assertEqual(result["total_positive_candidate_observations"],1)
        self.assertFalse(result["trade_allowed"])
    def test_rejects_unverified_timestamp_or_claimed_rule_verification(self):
        mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                 "market_rules_verified":True,"opposing_token_map":{}}
        with self.assertRaises(ValueError):
            build({"captured_at":"2026-10-28T20:00:00Z","rows":[]},mapping)
        mapping["market_rules_verified"]=False
        with self.assertRaises(ValueError):
            build({"captured_at":"2026-10-28T20:00:00","rows":[]},mapping)
if __name__=="__main__":
    unittest.main()
