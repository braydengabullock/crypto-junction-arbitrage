import unittest
from one_event_pair_combinations import combinations

class PairCombinationTests(unittest.TestCase):
    def test_cross_pairing_and_missing_quote(self):
        r={"exact_outcome_candidates":[
              {"team":"OKC","kalshi_ticker":"K-OKC","polymarket_token_id":"11"},
              {"team":"DAL","kalshi_ticker":"K-DAL","polymarket_token_id":"22"}],
           "book_probes":[{"venue":"kalshi","ticker":"K-OKC","yes_buy_best_ask":"0.67"},
                          {"venue":"kalshi","ticker":"K-DAL","yes_buy_best_ask":"0.34"}]}
        r["polymarket_contracts"]=[{"outcomes":'["Thunder","Mavericks"]',
            "clobTokenIds":'["11","22"]', "indicative_outcome_prices":'["0.655","0.345"]'}]
        out=combinations(r)
        self.assertEqual(out["combinations"][0]["indicative_pair_cost_per_contract_before_fees"],"1.015")
        self.assertEqual(out["combinations"][1]["indicative_pair_cost_per_contract_before_fees"],"0.995")
        self.assertTrue(out["combinations"][0]["indicative_screen_only_not_executable"])
        self.assertEqual(len(out["combinations"]),2)
        self.assertEqual(out["combinations"][0]["polymarket_team"],"DAL")
        self.assertEqual(out["combinations"][1]["polymarket_team"],"OKC")
        self.assertTrue(all(x["status"]=="PRICE_EVIDENCE_INCOMPLETE" for x in out["combinations"]))
        self.assertFalse(out["net_roi_verified"])
    def test_no_partial_pair(self):
        out=combinations({"exact_outcome_candidates":[{"team":"OKC"}]})
        self.assertEqual(out["combinations"],[])
if __name__=="__main__": unittest.main()
