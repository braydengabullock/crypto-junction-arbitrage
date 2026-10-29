import unittest
from historical_audit import evaluate, audit

def sample():
    return {
        "id":"example","source_a":"Kalshi","source_b":"Polymarket",
        "side_a":"YES","side_b":"NO","ask_a":"0.40","ask_b":"0.53",
        "fee_a_per_contract":"0.01","fee_b_per_contract":"0.01",
        "depth_a":100,"depth_b":100,
        "verified_rule_equivalence":True,
        "verified_execution_quotes":True,
        "verified_trading_eligibility":True,
        "verified_settlement":True,
        "actual_payout_per_pair":"1.00",
        "observed_quote_time_a":"2026-10-28T15:00:00Z",
        "observed_quote_time_b":"2026-10-28T15:00:01Z",
        "actual_settlement_time":"2026-10-28T16:00:00Z"}
class HistoricalAuditTests(unittest.TestCase):
    def test_example_is_only_conditional(self):
        r=evaluate(sample())
        self.assertEqual(r["status"],"CONDITIONAL_PAPER_RESULT")
        self.assertEqual(r["contracts_per_leg"],100)
        self.assertEqual(r["modeled_profit_usd"],"5.00")
        self.assertIsNone(audit([sample()])["actual_realized_profit_usd"])
    def test_missing_evidence_blocks(self):
        p=sample();del p["verified_settlement"]
        self.assertEqual(evaluate(p)["status"],"INSUFFICIENT_EVIDENCE")
    def test_unverified_rules_block(self):
        p=sample();p["verified_rule_equivalence"]=False
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_stale_pair_blocks(self):
        p=sample();p["observed_quote_time_b"]="2026-10-28T15:10:00Z"
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_depth_blocks(self):
        p=sample();p["depth_a"]=0
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_low_roi_blocks(self):
        p=sample();p["ask_b"]="0.60"
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_small_positive_below_two_percent_is_allowed(self):
        p=sample();p["ask_b"]="0.575"
        r=evaluate(p)
        self.assertEqual(r["status"],"CONDITIONAL_PAPER_RESULT")
        self.assertGreater(float(r["entry_projected_roi_pct"]),0)
        self.assertLess(float(r["entry_projected_roi_pct"]),2)
    def test_venue_caps_and_no_larger_budget(self):
        p=sample();p["depth_a"]=10000;p["depth_b"]=10000
        r=evaluate(p)
        self.assertEqual(r["status"],"CONDITIONAL_PAPER_RESULT")
        self.assertLessEqual(r["contracts_per_leg"]*0.41,2500)
        self.assertLessEqual(r["contracts_per_leg"]*0.54,2500)
        self.assertEqual(evaluate(p,budget="5001")["status"],"INSUFFICIENT_EVIDENCE")
    def test_actual_loss_is_counted_when_entry_looked_profitable(self):
        p=sample()
        p["actual_payout_per_pair"]="0.50"
        result=evaluate(p)
        self.assertEqual(result["status"],"CONDITIONAL_PAPER_RESULT")
        self.assertEqual(result["modeled_profit_usd"],"-45.00")
        summary=audit([p])
        self.assertEqual(summary["conditional_losses"],1)
        self.assertEqual(summary["conditional_wins"],0)
    def test_settlement_outside_two_hours_blocked(self):
        p=sample()
        p["actual_settlement_time"]="2026-10-28T18:00:02Z"
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_cash_reuse_is_never_assumed(self):
        self.assertIs(evaluate(sample())["cash_reuse_verified"],False)
    def test_payout_above_one_dollar_rejected(self):
        p=sample()
        p["actual_payout_per_pair"]="1.25"
        self.assertEqual(evaluate(p)["status"],"NOT_VALIDATED")
    def test_budget(self):
        r=evaluate(sample(),budget="50")
        self.assertEqual(r["contracts_per_leg"],52)
        self.assertEqual(r["modeled_cost_usd"],"49.40")
    def test_never_report_earnings_on_empty_data(self):
        r=audit([])
        self.assertEqual(r["observations"],0)
        self.assertIsNone(r["actual_realized_profit_usd"])
if __name__=="__main__":
    unittest.main()
