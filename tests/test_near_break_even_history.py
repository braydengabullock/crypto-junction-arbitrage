import unittest
from near_break_even_history import update

def row(net,streak=0):
    return {"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"T",
            "fixed_ten_current_net_usd":net,"near_break_even_streak":streak,"quote_quality_passed":True}

class PersistenceTests(unittest.TestCase):
    def test_continues_close_streak(self):
        result=update({"changes":[row("-0.20",2)]},{"changes":[row("-0.10")]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],3)
        self.assertEqual(result["persistent_near_break_even_pairs"],1)

    def test_resets_when_no_longer_close(self):
        result=update({"changes":[row("-0.20",3)]},{"changes":[row("-0.30")]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],0)
        self.assertEqual(result["persistent_near_break_even_pairs"],0)

    def test_does_not_transfer_between_different_pairs(self):
        old=row("-0.20",4)
        new=row("-0.10")
        new["polymarket_token_id"]="OTHER"
        result=update({"changes":[old]},{"changes":[new]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],1)

    def test_quality_failure_resets_streak(self):
        old=row("-0.20",4)
        current=row("-0.10")
        current["quote_quality_passed"]=False
        result=update({"changes":[old]},{"changes":[current]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],0)
        self.assertEqual(result["persistent_near_break_even_pairs"],0)

    def test_shortlist_prioritizes_quality_over_closer_gap(self):
        weak=row("-0.01",5)
        weak.update(kalshi_ticker="WEAK",quote_quality_passed=False,
                    distance_to_break_even_fixed_ten_usd="0.01")
        strong=row("-0.20",0)
        strong.update(kalshi_ticker="STRONG",quote_quality_passed=True,
                      distance_to_break_even_fixed_ten_usd="0.20")
        result=update({"changes":[]},{"changes":[weak,strong]})
        self.assertEqual(result["research_shortlist"][0]["kalshi_ticker"],"STRONG")
        self.assertEqual(result["shortlist_quality_passed"],1)
        self.assertEqual(result["shortlist_quality_unverified"],1)

    def test_missing_fixed_benchmark_excluded_from_shortlist(self):
        missing=row(None)
        missing["distance_to_break_even_fixed_ten_usd"]=None
        result=update({"changes":[]},{"changes":[missing]})
        self.assertEqual(result["research_shortlist"],[])
        self.assertEqual(result["shortlist_quality_passed"],0)

    def test_missing_fixed_quote_resets(self):
        result=update({"changes":[row("-0.20",4)]},{"changes":[row(None)]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],0)

if __name__=="__main__":
    unittest.main()
