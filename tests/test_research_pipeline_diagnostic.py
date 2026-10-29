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
        self.assertTrue(r["partial_market_data_coverage"])
        self.assertEqual(r["rows_with_both_venue_observations"],1)
        self.assertEqual(r["rows_with_incomplete_venue_observations"],1)
        self.assertEqual(r["positive_modeled_profit_candidates"],0)
        self.assertEqual(r["verified_opportunities"],0)
        self.assertEqual(r["primary_research_bottleneck"],"NO_POSITIVE_MODELED_RETURNS")
        self.assertFalse(r["trade_allowed"])
    def test_empty_outputs_stay_unverified(self):
        r=diagnose({"rows":[]},{"rows":[],"near_misses":[]},{}, {})
        self.assertEqual(r["rows_sampled"],0)
        self.assertEqual(r["primary_research_bottleneck"],"NO_BOOK_SAMPLES")
        self.assertEqual(r["capital_audit_status"],"UNKNOWN")
        self.assertEqual(r["verified_opportunities"],0)
    def test_missing_books_not_called_unprofitable(self):
        books={"rows":[{"observations":[{"venue":"kalshi"}],"errors":[]}]}
        r=diagnose(books,{"status":"ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES","near_misses":[],"rows":[]},{},{})
        self.assertEqual(r["primary_research_bottleneck"],"MISSING_BOOK_DATA")
        self.assertIn("fetch errors",r["next_research_action"])
    def test_missing_outcome_mapping_not_called_unprofitable(self):
        books={"rows":[{"observations":[{"venue":"kalshi"},{"venue":"polymarket"}],"errors":[]}]}
        r=diagnose(books,{"status":"OPPOSING_OUTCOME_MAPPING_REQUIRED","near_misses":[],"rows":[]},{},{})
        self.assertEqual(r["primary_research_bottleneck"],"MISSING_OUTCOME_MAPPING")
        self.assertIn("outcome labels",r["next_research_action"])
    def test_all_positive_scenarios_do_not_hide_partial_book_coverage(self):
        books={"rows":[{"observations":[{"venue":"kalshi"},{"venue":"polymarket"}],"errors":[]},
                       {"observations":[{"venue":"kalshi"}],"errors":[]}]}
        pricing={"status":"ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES",
                 "near_misses":[{"scenario":{"net_roi_tier":"EXCEPTIONAL_2_PLUS"}}],
                 "rows":[{"scenario":{"net_roi_tier":"EXCEPTIONAL_2_PLUS"}}]}
        r=diagnose(books,pricing,{"capital_audit_passed":True},{})
        self.assertEqual(r["mapped_pairs_with_modeled_costs"],1)
        self.assertEqual(r["nonpositive_priced_pairs"],0)
        self.assertTrue(r["partial_market_data_coverage"])
        self.assertEqual(r["primary_research_bottleneck"],"REQUIRES_INDEPENDENT_VERIFICATION")
        self.assertEqual(r["verified_opportunities"],0)
    def test_unpriced_books_cause_uncertain(self):
        books={"rows":[{"observations":[{"venue":"kalshi"},{"venue":"polymarket"}],"errors":[]}]}
        r=diagnose(books,{"status":"ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES","near_misses":[],"rows":[]},{},{})
        self.assertEqual(r["primary_research_bottleneck"],"NO_PRICED_PAIRS_UNDETERMINED_CAUSE")
if __name__=="__main__":
    unittest.main()
