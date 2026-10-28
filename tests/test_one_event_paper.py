import unittest
from one_event_paper import compare_one
K={"orderbook_fp":{"no_dollars":[["0.60","100"]],"yes_dollars":[]}}
P={"asks":[{"price":"0.50","size":"100"}]}
class OneEventPaperTests(unittest.TestCase):
    def test_paper_math_never_implies_real_trade(self):
        result=compare_one(ticker="TEST",token_id="123",kalshi_side="YES",
            fee_kalshi="0.01",fee_polymarket="0.01",other_cost_usd="0",
            fetch_k=lambda _:K,fetch_p=lambda _:P)
        self.assertTrue(result["paper_review"]["scenarios"])
        self.assertFalse(result["paper_review"]["trade_allowed"])
        self.assertFalse(result["matching_rules_verified"])
    def test_non_numeric_token_rejected(self):
        with self.assertRaises(ValueError):
            compare_one(ticker="TEST",token_id="bad",kalshi_side="YES",
                fee_kalshi="0",fee_polymarket="0",other_cost_usd="0")
if __name__=="__main__":
    unittest.main()
