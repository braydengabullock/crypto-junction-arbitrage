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
    def test_unrelated(self):
        a={"markets":[{"ticker":"A","title":"Bitcoin halving next year"}]}
        b={"markets":[{"id":"B","question":"Oscar best picture winner"}]}
        self.assertEqual(compare(a,b)[1],0)
    def test_no_title(self):
        self.assertEqual(compare({"markets":[{}]},{"markets":[{}]})[1],0)
if __name__=="__main__":
    unittest.main()
