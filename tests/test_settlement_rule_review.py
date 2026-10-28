import unittest
from settlement_rule_review import build,enrich,CHECKS

class SettlementReviewTests(unittest.TestCase):
    def test_each_pair_requires_independent_rule_evidence(self):
        report=build({"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                      "opposing_token_map":{"GAME|YES":"123","GAME|NO":"456"}})
        self.assertEqual(len(report["review_records"]),2)
        self.assertEqual(report["verified_pairs"],0)
        self.assertFalse(report["trade_allowed"])
        for row in report["review_records"]:
            self.assertEqual(row["status"],"UNVERIFIED_RULES")
            self.assertFalse(row["rule_equivalence_verified"])
            self.assertEqual(set(row["review_required"]),set(CHECKS))
            self.assertIsNone(row["kalshi_rule_source_url"])
            self.assertIsNone(row["polymarket_rule_source_url"])

    def test_title_matching_cannot_approve_rules(self):
        with self.assertRaises(ValueError):
            build({"mapping_method":"title_similarity","opposing_token_map":{"G|YES":"1"}})

    def test_missing_mapping_rejected(self):
        with self.assertRaises(ValueError):
            build({"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels"})

    def test_snapshot_rule_texts_collected_without_approval(self):
        mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                 "opposing_token_map":{"GAME|YES":"123"}}
        kalshi={"markets":[{"ticker":"GAME","rules_primary":"Official result after overtime"}]}
        polymarket={"markets":[{"id":"77","slug":"game-77",
                    "clobTokenIds":'["123","456"]',
                    "description":"Regulation result only",
                    "resolutionSource":"League statistics"}]}
        result=enrich(build(mapping),kalshi,polymarket)
        row=result["review_records"][0]
        self.assertTrue(row["source_fields_collected"])
        self.assertEqual(row["status"],"RULE_TEXT_COLLECTED_REVIEW_REQUIRED")
        self.assertEqual(result["records_with_both_rule_texts"],1)
        self.assertFalse(row["rule_equivalence_verified"])
        self.assertEqual(result["verified_pairs"],0)
        self.assertIn("Regulation",row["polymarket_rule_text"])

    def test_missing_source_fails_closed(self):
        mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                 "opposing_token_map":{"GAME|YES":"123"}}
        result=enrich(build(mapping),{"markets":[]},{"markets":[]})
        self.assertEqual(result["records_with_both_rule_texts"],0)
        self.assertEqual(result["review_records"][0]["status"],"RULE_EVIDENCE_INCOMPLETE")
        self.assertFalse(result["review_records"][0]["rule_equivalence_verified"])

    def test_malformed_entries_excluded(self):
        report=build({"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
                      "opposing_token_map":{"BAD":"123","G|MAYBE":"456","G|YES":"789"}})
        self.assertEqual(len(report["review_records"]),1)
        self.assertEqual(report["review_records"][0]["polymarket_token_id"],"789")

if __name__=="__main__":
    unittest.main()
