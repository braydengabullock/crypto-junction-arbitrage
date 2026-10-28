import unittest
from depth_pair_review import review
K={"orderbook_fp":{"no_dollars":[["0.60","100"]],"yes_dollars":[]}}
P={"asks":[{"price":"0.50","size":"100"}]}
T="2026-10-28T12:00:00Z"
class DepthPairTests(unittest.TestCase):
    def test_budget_and_research_only(self):
        r=review(K,P,kalshi_side="YES",observed_kalshi=T,
                 observed_polymarket=T,fee_kalshi="0.01",fee_polymarket="0.01")
        self.assertFalse(r["trade_allowed"])
        self.assertFalse(r["validated_opportunity"])
        self.assertTrue(r["scenarios"])
        self.assertLessEqual(float(r["largest_displayed_scenario"]["displayed_cost_usd"]),100)
    def test_missing_fee_blocks(self):
        self.assertFalse(review(K,P,kalshi_side="YES",observed_kalshi=T,
                      observed_polymarket=T)["scenarios"])
    def test_unsynchronized_blocks(self):
        self.assertFalse(review(K,P,kalshi_side="YES",observed_kalshi=T,
                      observed_polymarket="2026-10-28T12:01:00Z",
                      fee_kalshi="0",fee_polymarket="0")["scenarios"])
    def test_no_depth_blocks(self):
        self.assertFalse(review({"orderbook_fp":{"no_dollars":[]}},P,
                      kalshi_side="YES",observed_kalshi=T,observed_polymarket=T,
                      fee_kalshi="0",fee_polymarket="0")["scenarios"])
    def test_over_budget_blocks(self):
        self.assertFalse(review(K,P,kalshi_side="YES",observed_kalshi=T,
                      observed_polymarket=T,fee_kalshi="0",fee_polymarket="0",
                      budget="101")["scenarios"])
if __name__=="__main__":
    unittest.main()
