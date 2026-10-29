import unittest
from research_pipeline_diagnostic import diagnose

class PipelineDiagnosticTests(unittest.TestCase):
    def test_reports_missing_books_without_claiming_trades(self):
        books={"rows":[{"observations":[{"venue":"kalshi"}],"errors":["Polymarket HTTP 404"]},
                       {"observations":[{"venue":"kalshi"},{"venue":"polymarket"}],"errors":[]}]}
        pricing={"status":"ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES","near_misses":[{"scenario":{"net_roi_tier":"NONPOSITIVE_REJECT"}}],
                 "rows":[],"fx_cost_supplied":False}
        audit={"evidence_status":"VALIDATED_SAMPLE","scenarios_checked":1,"issues":[]}
        eff={"matched_scenarios_compared":0}
        r=diagnose(books,pricing,audit,eff)
        self.assertEqual(r["rows_sampled"],2)
        self.assertEqual(r["book_collection_categories"]["MISSING_ONE_OR_BOTH_BOOKS"],1)
        self.assertEqual(r["nonpositive_priced_pairs"],1)
        self.assertEqual(r["positive_modeled_profit_candidates"],0)
        self.assertEqual(r["verified_opportunities"],0)
        self.assertFalse(r["trade_allowed"])
    def test_empty_outputs_stay_unverified(self):
        r=diagnose({"rows":[]},{"rows":[],"near_misses":[]},{}, {})
        self.assertEqual(r["rows_sampled"],0)
        self.assertEqual(r["capital_audit_status"],"UNKNOWN")
        self.assertEqual(r["verified_opportunities"],0)
if __name__=="__main__":
    unittest.main()
