"""Offline integration: depth screening -> funding audit; no network or trading."""
import unittest
from decimal import Decimal
from depth_fee_screen import screen
from capital_audit import audit

class ScreeningAuditIntegrationTests(unittest.TestCase):
    def test_positive_candidate_passes_independent_audit(self):
        books={"rows":[{"kalshi_ticker":"SYNTHETIC","observations":[
            {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.65","5000"]],"yes_dollars":[]}}},
            {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.50","size":"5000"}]}}]}]}
        result=screen(books,poly_rate="0",kalshi_multiplier="0",extra_cost="0",
                      fx_cost="0",budget="5000",per_venue_budget="2500",
                      opposing_tokens={"SYNTHETIC|YES":"123"})
        self.assertTrue(result["rows"])
        best=result["rows"][0]["scenario"]
        alloc=best["venue_allocation"]
        self.assertGreater(Decimal(best["hypothetical_net_usd"]),0)
        self.assertLessEqual(Decimal(alloc["kalshi_conservative_funding_reserve_usd"]),2500)
        self.assertLessEqual(Decimal(alloc["polymarket_conservative_funding_reserve_usd"]),2500)
        evidence=audit(result)
        self.assertEqual(evidence["evidence_status"],"VALIDATED_SAMPLE")
        self.assertTrue(evidence["capital_audit_passed"])
        self.assertFalse(result["trade_allowed"])
        self.assertFalse(evidence["trade_allowed"])

    def test_missing_outcome_map_cannot_validate_candidates(self):
        result=screen({"rows":[]},poly_rate="0",kalshi_multiplier="0",
                      extra_cost="0",budget="5000")
        evidence=audit(result)
        self.assertEqual(result["status"],"OPPOSING_OUTCOME_MAPPING_REQUIRED")
        self.assertEqual(evidence["evidence_status"],"NO_SCENARIOS")
        self.assertFalse(evidence["capital_audit_passed"])

if __name__=="__main__":
    unittest.main()
