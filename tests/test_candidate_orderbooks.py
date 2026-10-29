import unittest
from candidate_orderbooks import collect,parse_tokens

class CandidateBookTests(unittest.TestCase):
    def test_token_list(self):
        self.assertEqual(parse_tokens('["123","456"]'),["123","456"])
        self.assertEqual(parse_tokens("broken"),[])
    def test_empty(self):
        self.assertEqual(collect([])["sampled_candidates"],0)
    def test_fetches_and_never_verifies(self):
        r=collect([{"kalshi_ticker":"K","polymarket_id":"P",
                     "polymarket_clob_token_ids":'["123","456"]'}],
                  fetch_k=lambda _:{"orderbook_fp":{}},
                  fetch_p=lambda _:{"asks":[]})
        self.assertEqual(len(r["rows"][0]["observations"]),3)
        for observation in r["rows"][0]["observations"]:
            self.assertIn("request_started_at",observation)
            self.assertIn("observed_at",observation)
        self.assertEqual(r["verified_opportunities"],0)
        self.assertFalse(r["rows"][0]["executable_opportunity_verified"])
    def test_failure_is_visible(self):
        def fail(_): raise RuntimeError("no data")
        r=collect([{"kalshi_ticker":"K",
                    "polymarket_clob_token_ids":'["123"]'}],
                   fetch_k=fail,fetch_p=fail)
        self.assertEqual(len(r["rows"][0]["errors"]),2)
        self.assertEqual(len(r["rows"][0]["observations"]),0)
    def test_collection_diagnostics_distinguish_missing_books(self):
        candidates=[
            {"kalshi_ticker":"KXNBAGAME-26OCT28OKCDAL-OKC",
             "polymarket_clob_token_ids":'["123"]'},
            {"kalshi_ticker":"KXNHLGAME-26OCT28BOSTOR-BOS",
             "polymarket_clob_token_ids":'["456"]'}]
        def fetch_k(ticker):
            if "NHL" in ticker: raise RuntimeError("unavailable")
            return {"orderbook_fp":{}}
        def fetch_p(token):
            if token=="123": raise RuntimeError("unavailable")
            return {"asks":[]}
        r=collect(candidates,fetch_k=fetch_k,fetch_p=fetch_p)
        self.assertEqual(r["collection_diagnostics"]["POLYMARKET_BOOK_MISSING"],1)
        self.assertEqual(r["collection_diagnostics"]["KALSHI_BOOK_MISSING"],1)
        self.assertEqual(r["collection_diagnostics_by_league"]["NBA"]["POLYMARKET_BOOK_MISSING"],1)
        self.assertEqual(r["collection_diagnostics_by_league"]["NHL"]["KALSHI_BOOK_MISSING"],1)
        self.assertEqual(r["verified_opportunities"],0)

    def test_unsampled_candidates_and_missing_ids(self):
        candidates=[{"kalshi_ticker":"KXNBAGAME-26OCT28OKCDAL-OKC",
                     "polymarket_clob_token_ids":None},
                    {"kalshi_ticker":"KXNHLGAME-26OCT28BOSTOR-BOS",
                     "polymarket_clob_token_ids":'["123"]'}]
        r=collect(candidates,max_pairs=1)
        self.assertEqual(r["unsampled_eligible_candidates"],1)
        self.assertEqual(r["collection_diagnostics"]["MISSING_IDENTIFIERS"],1)

    def test_maximum_30_paired_snapshots_remains_bounded(self):
        candidates=[{"kalshi_ticker":f"KXNBAGAME-26OCT28AB{i}-A",
                     "polymarket_clob_token_ids":'["123"]'} for i in range(35)]
        r=collect(candidates,max_pairs=30,fetch_k=lambda _ :{"orderbook_fp":{}},
                  fetch_p=lambda _ :{"asks":[]})
        self.assertEqual(r["sampled_candidates"],30)
        self.assertEqual(r["unsampled_eligible_candidates"],5)
        with self.assertRaises(ValueError):
            collect(candidates,max_pairs=31)
    def test_parallel_capture_preserves_pair_order_and_timestamps(self):
        candidates=[{"kalshi_ticker":f"K{i}","polymarket_clob_token_ids":'["123"]'} for i in range(4)]
        result=collect(candidates,max_pairs=4,workers=2,
            fetch_k=lambda _ :{"orderbook_fp":{}},fetch_p=lambda _ :{"asks":[]})
        self.assertEqual(result["worker_count"],2)
        self.assertEqual([r["kalshi_ticker"] for r in result["rows"]],[f"K{i}" for i in range(4)])
        self.assertTrue(all(len(r["observations"])==2 for r in result["rows"]))
        with self.assertRaises(ValueError):
            collect(candidates,workers=5)
    def test_no_tokens_no_request(self):
        r=collect([{"kalshi_ticker":"K","polymarket_clob_token_ids":None}])
        self.assertTrue(r["rows"][0]["errors"])
if __name__=="__main__":
    unittest.main()
