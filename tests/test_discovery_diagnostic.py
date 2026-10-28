import unittest
from discovery_diagnostic import diagnose

class DiscoveryDiagnosticTests(unittest.TestCase):
    def test_category_imbalance_and_near_matches(self):
        k={"markets":[{"ticker":"K","title":"NBA Celtics beat Knicks"}],
           "data_quality":{"pagination":{"complete":False}}}
        p={"markets":[{"id":"P","question":"Will Celtics defeat Knicks in NBA game?"}],
           "data_quality":{"pagination":{"complete":False}}}
        result=diagnose(k,p)
        self.assertEqual(result["sports_keyword_markets"]["kalshi"],1)
        self.assertEqual(result["sports_keyword_markets"]["polymarket"],1)
        self.assertTrue(result["near_match_examples_unverified"])
        self.assertFalse(result["near_match_examples_unverified"][0]["rule_equivalence_verified"])
    def test_unrelated_markets_have_no_near_matches(self):
        result=diagnose({"markets":[{"title":"Bitcoin halving"}]},
                        {"markets":[{"question":"Oscar winners"}]})
        self.assertEqual(result["near_match_candidate_count"],0)
if __name__=="__main__":
    unittest.main()
