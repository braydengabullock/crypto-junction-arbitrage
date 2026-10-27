import unittest
from capital_limits import capital_check

class CapitalTests(unittest.TestCase):
    def setUp(self):
        self.r={"allocation_a_usd":"42.00","allocation_b_usd":"53.00"}
    def test_allowed_when_balances_and_reserves_sufficient(self):
        result=capital_check(self.r,balance_a=200,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertTrue(result["allowed"])
    def test_block_underfunded_venue(self):
        result=capital_check(self.r,balance_a=50,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])
    def test_block_aggregate_exposure(self):
        result=capital_check(self.r,balance_a=200,balance_b=200,portfolio_total=1000,total_current_committed=200)
        self.assertFalse(result["allowed"])
    def test_block_missing_balance(self):
        result=capital_check(self.r,balance_a=None,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])
    def test_block_negative_values(self):
        result=capital_check(self.r,balance_a=-1,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])

if __name__=="__main__":
    unittest.main()
