import unittest
from settlement_rule_triage import triage

class RuleTriageTests(unittest.TestCase):
    def test_different_overtime_mentions_flagged(self):
        result=triage({"review_records":[{"kalshi_ticker":"K","kalshi_side":"YES",
             "polymarket_token_id":"1","source_fields_collected":True,
             "kalshi_rule_text":"Includes overtime","polymarket_rule_text":"Final score"}]})
        self.assertEqual(result["records_with_text_mention_differences"],1)
        self.assertEqual(result["records"][0]["manual_review_flags"][0]["topic"],"overtime")
        self.assertFalse(result["records"][0]["rule_equivalence_verified"])
    def test_same_mentions_still_require_review(self):
        result=triage({"review_records":[{"kalshi_rule_text":"Includes overtime",
              "polymarket_rule_text":"Excludes overtime","source_fields_collected":True}]})
        self.assertEqual(result["records_with_text_mention_differences"],0)
        self.assertEqual(result["records"][0]["manual_review_priority"],"READ_BOTH_RULES")
        self.assertEqual(result["verified_pairs"],0)
    def test_postponement_difference_stays_potential(self):
        result=triage({"review_records":[{
            "kalshi_rule_text":"If postponed more than 48 hours, fair price",
            "polymarket_rule_text":"If postponed, market remains open until played",
            "source_fields_collected":True}]})
        row=result["records"][0]
        self.assertEqual(row["opportunity_class"],"POTENTIAL_ARBITRAGE")
        self.assertIn("POSSIBLE_POSTPONEMENT_WINDOW_MISMATCH",row["settlement_risk_flags"])
        self.assertFalse(result["trade_allowed"])
    def test_missing_text_does_not_verify(self):
        result=triage({"review_records":[{}]})
        self.assertFalse(result["records"][0]["rule_texts_collected"])
        self.assertFalse(result["trade_allowed"])
if __name__=="__main__":
    unittest.main()
