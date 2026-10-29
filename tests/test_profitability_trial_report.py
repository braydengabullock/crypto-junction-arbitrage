import unittest
from profitability_trial_report import evaluate

def sample(roi=True,window=True,depth=True):
    s={"contracts_each":20,"total_cost_usd":"18","hypothetical_net_usd":"2" if roi else "0.1"}
    key={"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"P"}
    return {"rows":[dict(key,scenario=s)],"near_misses":[dict(key,quote_quality={"within_20_seconds":window,"sufficient_depth_for_ten":depth})]}

class ProfitabilityTrialTests(unittest.TestCase):
    def test_positive_model_is_not_verified(self):
        out=evaluate(sample())
        self.assertEqual(out["candidate_pairs_eligible_for_research"],1)
        self.assertEqual(out["positive_candidates_with_short_window_and_ten_contract_depth"],1)
        self.assertEqual(out["verified_profitable_opportunities"],0)
        self.assertFalse(out["trade_allowed"])
    def test_stale_quote_does_not_pass_quality(self):
        out=evaluate(sample(window=False))
        self.assertEqual(out["candidate_pairs_at_least_2_pct_modeled_roi"],1)
        self.assertEqual(out["positive_candidates_with_short_quote_window"],0)
    def test_small_positive_return_is_still_included(self):
        out=evaluate(sample(roi=False))
        self.assertEqual(out["candidate_pairs_at_least_2_pct_modeled_roi"],0)
    def test_missing_qualifying_sample(self):
        out=evaluate({"rows":[],"near_misses":[]})
        self.assertEqual(out["conclusion"],"NO_POSITIVE_MODELED_CANDIDATES_IN_THIS_SAMPLE")
if __name__=="__main__":
    unittest.main()
