import unittest
from market_comparison import compare

class ComparisonTests(unittest.TestCase):
    def test_identical_titles_are_only_research(self):
        k={"markets":[{"ticker":"K1","title":"Will Bitcoin exceed 100000 in 2027?"}]}
        p={"markets":[{"id":"P1","slug":"btc","question":"Will Bitcoin exceed 100000 in 2027?"}]}
        matches,count=compare(k,p)
        self.assertEqual(count,1)
        self.assertEqual(matches[0]["status"],"MANUAL_REVIEW_ONLY")
        self.assertFalse(matches[0]["market_rules_verified"])
        self.assertFalse(matches[0]["price_comparison_verified"])
        self.assertFalse(matches[0]["tradable"])
        self.assertNotIn("profit",matches[0])
    def test_review_queue_preserves_raw_evidence_without_verifying(self):
        a={"markets":[{"ticker":"K","title":"Will gold exceed 3000 in 2027?",
                       "rules_primary":"Official Kalshi rule excerpt",
                       "expiration_time":"2027-01-01T00:00:00Z"}]}
        b={"markets":[{"id":"P","question":"Will gold exceed 3000 in 2027?",
                       "description":"Public Polymarket description",
                       "resolutionSource":"Example source",
                       "endDate":"2027-01-01T00:00:00Z",
                       "clobTokenIds":'["111","222"]'}]}
        matches,_=compare(a,b)
        self.assertEqual(matches[0]["kalshi_rules_excerpt"],"Official Kalshi rule excerpt")
        self.assertEqual(matches[0]["polymarket_resolution_source"],"Example source")
        self.assertIsNone(matches[0]["kalshi_rule_url"])
        self.assertFalse(matches[0]["market_rules_verified"])
        self.assertGreater(len(matches[0]["review_required"]),0)
    def test_sports_subtitle_is_discoverable_but_never_verified(self):
        k={"markets":[{"ticker":"K-NBA","title":"NBA game winner",
                       "subtitle":"Boston Celtics versus New York Knicks"}]}
        p={"markets":[{"id":"P-NBA","question":"Will Boston Celtics beat New York Knicks?"}]}
        matches,count=compare(k,p)
        self.assertGreaterEqual(count,1)
        self.assertTrue(matches[0]["sports_candidate"])
        self.assertFalse(matches[0]["market_rules_verified"])
        self.assertFalse(matches[0]["tradable"])
    def test_one_shared_team_name_is_not_enough(self):
        k={"markets":[{"ticker":"K","title":"Boston Celtics game"}]}
        p={"markets":[{"id":"P","question":"Boston Bruins Stanley Cup"}]}
        self.assertEqual(compare(k,p)[1],0)
    def test_unrelated(self):
        a={"markets":[{"ticker":"A","title":"Bitcoin halving next year"}]}
        b={"markets":[{"id":"B","question":"Oscar best picture winner"}]}
        self.assertEqual(compare(a,b)[1],0)
    def test_no_title(self):
        self.assertEqual(compare({"markets":[{}]},{"markets":[{}]})[1],0)
if __name__=="__main__":
    unittest.main()
