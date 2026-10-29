import unittest
from capital_efficiency import compare

class CapitalEfficiencyTests(unittest.TestCase):
    def test_incremental_capital_yield(self):
        r=compare({"rows":[{"kalshi_ticker":"K","scenario":{"contracts_each":100,"total_cost_usd":"90","hypothetical_net_usd":"10"},
                            "max_roi_scenario":{"contracts_each":20,"total_cost_usd":"16","hypothetical_net_usd":"4"}}]})
        x=r["comparisons"][0]
        self.assertEqual(x["additional_capital_usd"],"74")
        self.assertEqual(x["additional_modeled_profit_usd"],"6")
        self.assertEqual(x["incremental_modeled_roi_pct"],"8.108")
        self.assertFalse(r["trade_allowed"])
    def test_equal_sizes_have_no_marginal_yield(self):
        s={"contracts_each":10,"total_cost_usd":"8","hypothetical_net_usd":"2"}
        r=compare({"rows":[{"scenario":s,"max_roi_scenario":s}]})
        self.assertTrue(r["comparisons"][0]["same_sizing"])
        self.assertIsNone(r["comparisons"][0]["incremental_modeled_roi_pct"])
    def test_no_positive_model_excluded(self):
        s={"contracts_each":10,"total_cost_usd":"11","hypothetical_net_usd":"-1"}
        self.assertEqual(compare({"rows":[{"scenario":s,"max_roi_scenario":s}]})["comparisons"],[])

if __name__=="__main__":
    unittest.main()
