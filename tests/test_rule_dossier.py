import unittest
from rule_dossier import review_rules, FIELDS

def example():
    data={k:"example" for k in FIELDS}
    data.update(
        observation_start_utc="2026-10-28T12:00:00Z",
        observation_end_utc="2026-10-28T13:00:00Z",
        payout_per_contract="1",
        official_rule_url="https://example.com/rules",
        verified_by_human=True,
        selected_side="YES")
    return data

class RuleDossierTests(unittest.TestCase):
    def test_matched_summary_still_not_verified(self):
        a=example();b=example();b["selected_side"]="NO"
        outcome=review_rules(a,b)
        self.assertEqual(outcome["status"],"MANUAL_EVIDENCE_MATCH")
        self.assertFalse(outcome["settlement_equivalence_verified"])
    def test_different_source_rejected(self):
        a=example();b=example();b["selected_side"]="NO"
        b["measurement_source"]="different"
        self.assertEqual(review_rules(a,b)["status"],"BLOCKED")
    def test_different_window_rejected(self):
        a=example();b=example();b["selected_side"]="NO"
        b["observation_end_utc"]="2026-10-28T14:00:00Z"
        self.assertEqual(review_rules(a,b)["status"],"BLOCKED")
    def test_same_side_rejected(self):
        self.assertEqual(review_rules(example(),example())["status"],"BLOCKED")
    def test_no_primary_rules_rejected(self):
        a=example();b=example();b["selected_side"]="NO"
        b["official_rule_url"]=""
        self.assertEqual(review_rules(a,b)["status"],"BLOCKED")
    def test_mismatch_payout_rejected(self):
        a=example();b=example();b["selected_side"]="NO"
        b["payout_per_contract"]="0.5"
        self.assertEqual(review_rules(a,b)["status"],"BLOCKED")
if __name__=="__main__":
    unittest.main()
