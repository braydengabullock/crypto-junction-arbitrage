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

    def test_missing_fixed_quote_resets(self):
        result=update({"changes":[row("-0.20",4)]},{"changes":[row(None)]})
        self.assertEqual(result["changes"][0]["near_break_even_streak"],0)

if __name__=="__main__":
    unittest.main()
