import tempfile
import unittest
from pathlib import Path
from continuous_book_collector import record_once, run

def inputs():
    matches={"source":"kalshi_polymarket_title_research","research_only":True,
             "candidates":[{"kalshi_ticker":"K","polymarket_clob_token_ids":'["123"]'}]}
    mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
             "market_rules_verified":False,"opposing_token_map":{"K|YES":"123"}}
    return matches,mapping

class ContinuousCaptureTests(unittest.TestCase):
    def test_real_archive_shape_and_unique_files(self):
        matches,mapping=inputs()
        with tempfile.TemporaryDirectory() as d:
            for _ in range(2):
                r=record_once(matches,mapping,d,fetch_k=lambda _ :{"orderbook_fp":{}},
                              fetch_p=lambda _ :{"asks":[]})
                self.assertEqual(r["stored_book_rows"],1)
                self.assertFalse(r["trade_allowed"])
            self.assertEqual(len(list(Path(d).glob("*.json"))),2)
    def test_rejects_unbounded_or_too_fast_polling(self):
        matches,mapping=inputs()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run(matches,mapping,d,interval_seconds=1)
            with self.assertRaises(ValueError):
                run(matches,mapping,d,iterations=1441)
    def test_invalid_market_mapping_rejected(self):
        matches,mapping=inputs()
        mapping["market_rules_verified"]=True
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                record_once(matches,mapping,d)
if __name__=="__main__": unittest.main()
