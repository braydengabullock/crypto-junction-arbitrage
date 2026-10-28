import unittest
from opportunity_economics import diagnose

def pair(raw,friction,net):
    return {"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"1",
            "fixed_ten_contract_pairs":{"raw_displayed_spread_usd":raw,
                "modeled_total_friction_usd":friction,"hypothetical_net_usd":net}}

class EconomicsTests(unittest.TestCase):
    def test_distinguishes_price_gap_from_friction(self):
        r=diagnose({"near_misses":[pair("-0.1","0.2","-0.3"),
              pair("0.1","0.3","-0.2"),pair("0.5","0.2","0.3")]})
        self.assertEqual(r["fixed_ten_pairs_analyzed"],3)
        self.assertEqual(list(r["counts"].values()),[1,1,1])
        self.assertFalse(r["trade_allowed"])
    def test_league_breakdown_does_not_conflate_contract_sides(self):
        nba=pair("-0.1","0.2","-0.3")
        nba["kalshi_ticker"]="KXNBAGAME-26OCT28AAABBB-AAA"
        nhl=pair("0.1","0.3","-0.2")
        nhl["kalshi_ticker"]="KXNHLGAME-26OCT28AAABBB-AAA"
        result=diagnose({"near_misses":[nba,nhl]})
        self.assertEqual(result["by_league"]["NBA"]["pairs"],1)
        self.assertEqual(result["by_league"]["NHL"]["positive_raw_spread_pairs"],1)
        self.assertEqual(result["by_league"]["NHL"]["positive_illustrative_net_pairs"],0)
    def test_missing_benchmark_excluded(self):
        r=diagnose({"near_misses":[{"fixed_ten_contract_pairs":None}]})
        self.assertEqual(r["fixed_ten_pairs_analyzed"],0)
    def test_nonfinite_data_excluded(self):
        r=diagnose({"near_misses":[pair("NaN","1","0")]})
        self.assertEqual(r["fixed_ten_pairs_analyzed"],0)
if __name__=="__main__":
    unittest.main()
