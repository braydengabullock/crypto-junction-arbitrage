import unittest
from capital_limits import capital_check

class CapitalTests(unittest.TestCase):
    def setUp(self):
        self.r={"allocation_a_usd":"42.00","allocation_b_usd":"53.00"}
    def test_allowed_when_balances_and_reserves_sufficient(self):
        result=capital_check(self.r,balance_a=200,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertTrue(result["allowed"])
    def test_no_obsolete_percentage_cap(self):
        result=capital_check({"allocation_a_usd":"1800","allocation_b_usd":"1700"},
            balance_a=2500,balance_b=2500,portfolio_total=5000,total_current_committed=0)
        self.assertTrue(result["allowed"])
    def test_per_exchange_ceiling(self):
        result=capital_check({"allocation_a_usd":"2501","allocation_b_usd":"100"},
            balance_a=3000,balance_b=3000,portfolio_total=5000,total_current_committed=0)
        self.assertFalse(result["allowed"])
    def test_block_underfunded_venue(self):
        result=capital_check(self.r,balance_a=50,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])
    def test_block_aggregate_exposure(self):
        result=capital_check(self.r,balance_a=200,balance_b=200,portfolio_total=1000,total_current_committed=950)
        self.assertFalse(result["allowed"])
    def test_block_missing_balance(self):
        result=capital_check(self.r,balance_a=None,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])
    def test_block_negative_values(self):
        result=capital_check(self.r,balance_a=-1,balance_b=200,portfolio_total=1000,total_current_committed=0)
        self.assertFalse(result["allowed"])

if __name__=="__main__":
    unittest.main()
