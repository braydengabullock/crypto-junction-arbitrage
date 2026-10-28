import unittest
from phase1_real_data import report
class PhaseOneTests(unittest.TestCase):
    def test_counts_are_not_profit(self):
        m={"research_only":True,"potential_title_matches_found":12}
        q={"research_only":True,"rows_examined":5,
           "rows_with_kalshi_and_polymarket_books":3,
           "rows_with_synchronized_observations":2,
           "rows_with_displayed_depth_on_both_venues":1,
           "request_errors":2,"details":[]}
        r=report(m,q)
        self.assertEqual(r["title_match_candidates"],12)
        self.assertEqual(r["paired_books_collected"],3)
        self.assertIsNone(r["actual_profit_usd"])
        self.assertIsNone(r["projected_net_profit_usd"])
        self.assertEqual(r["verified_trade_opportunities"],0)
if __name__=="__main__":
    unittest.main()
