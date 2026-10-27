import unittest
from matching_review import candidates

class MatchingReviewTests(unittest.TestCase):
    def test_similar_titles_flagged_not_verified(self):
        a=[{"ticker":"A1","title":"Will Federal Reserve raise rates in October 2026?"}]
        b=[{"contract_id":"B1","title":"Federal Reserve raise rates October 2026"}]
        matches=candidates(a,b,0.5)
        self.assertEqual(len(matches),1)
        self.assertFalse(matches[0]["rule_match_verified"])
        self.assertEqual(matches[0]["status"],"MANUAL_REVIEW_REQUIRED")
    def test_unrelated_markets_do_not_match(self):
        self.assertEqual(candidates([{"title":"Bitcoin above 100000"}],[{"title":"Rainfall in London"}]),[])
    def test_bad_threshold(self):
        with self.assertRaises(ValueError):
            candidates([],[],1.2)

if __name__=="__main__":
    unittest.main()
