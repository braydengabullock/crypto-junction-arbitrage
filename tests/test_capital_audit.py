import unittest
from capital_audit import audit

def report(cost="20", gain="0", k="10", p="10"):
    s={"contracts_each":20,"total_cost_usd":cost,"hypothetical_net_usd":gain,
       "venue_allocation":{"kalshi_conservative_funding_reserve_usd":k,
                           "polymarket_conservative_funding_reserve_usd":p,
                           "kalshi_displayed_usd":"10","polymarket_displayed_usd":"10",
                           "modeled_fees_and_extra_usd":"0","assumed_fx_cost_usd":"0"}}
    return {"research_only":True,"max_combined_research_budget_usd":"5000",
            "max_per_venue_research_budget_usd":"2500",
            "rows":[{"scenario":s,"max_roi_scenario":s}],"near_misses":[]}

class CapitalAuditTests(unittest.TestCase):
    def test_valid_cap_and_arithmetic(self):
        r=audit(report())
        self.assertTrue(r["capital_audit_passed"])
        self.assertEqual(r["scenarios_checked"],2)
        self.assertFalse(r["trade_allowed"])
    def test_no_scenarios_is_not_validated_evidence(self):
        r=audit({"rows":[],"near_misses":[]})
        self.assertEqual(r["evidence_status"],"NO_SCENARIOS")
        self.assertFalse(r["capital_audit_passed"])
        self.assertFalse(r["trade_allowed"])
    def test_exceed_either_venue_limit(self):
        self.assertFalse(audit(report(k="2500.01"))["capital_audit_passed"])
        self.assertFalse(audit(report(p="2500.01"))["capital_audit_passed"])
    def test_exceed_combined_budget(self):
        self.assertFalse(audit(report(cost="5000.01"))["capital_audit_passed"])
    def test_net_accounting_inconsistent(self):
        self.assertFalse(audit(report(gain="0.01"))["capital_audit_passed"])
    def test_fractional_contract_quantity_rejected(self):
        sample=report()
        sample["rows"][0]["scenario"]["contracts_each"]="20.5"
        self.assertFalse(audit(sample)["capital_audit_passed"])
    def test_nonfinite_contract_quantity_rejected(self):
        sample=report()
        sample["rows"][0]["scenario"]["contracts_each"]="Infinity"
        self.assertFalse(audit(sample)["capital_audit_passed"])
    def test_cost_components_must_reconcile(self):
        sample=report()
        sample["rows"][0]["scenario"]["venue_allocation"]["assumed_fx_cost_usd"]="0.01"
        self.assertFalse(audit(sample)["capital_audit_passed"])
    def test_funding_reserve_cannot_be_less_than_purchase(self):
        self.assertFalse(audit(report(k="9.99"))["capital_audit_passed"])
        self.assertFalse(audit(report(p="9.99"))["capital_audit_passed"])
    def test_nonfinite_rejected(self):
        self.assertFalse(audit(report(k="NaN"))["capital_audit_passed"])

if __name__=="__main__":
    unittest.main()
