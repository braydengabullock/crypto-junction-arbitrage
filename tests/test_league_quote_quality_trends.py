import unittest
from league_quote_quality_trends import compare

class LeagueQuoteQualityTrendTests(unittest.TestCase):
    def test_rate_changes_are_percentage_points(self):
        old={"by_league":{"NBA":{"pairs":4,"quality_screen_passed_pairs":2}}}
        new={"by_league":{"NBA":{"pairs":5,"quality_screen_passed_pairs":4}}}
        row=compare(old,new)["by_league"]["NBA"]
        self.assertEqual(row["previous_pass_rate_pct"],50.0)
        self.assertEqual(row["current_pass_rate_pct"],80.0)
        self.assertEqual(row["change_percentage_points"],30.0)
        self.assertEqual(row["sample_change_pct"],25.0)
        self.assertEqual(row["interpretation"],"DESCRIPTIVE_ONLY_NOT_STABLE_TREND")
        self.assertEqual(row["status"],"COMPARABLE_RESEARCH")
    def test_zero_denominators_are_not_improvements(self):
        row=compare({"by_league":{}},{"by_league":{"NHL":{"pairs":2,"quality_screen_passed_pairs":1}}})["by_league"]["NHL"]
        self.assertIsNone(row["change_percentage_points"])
        self.assertEqual(row["status"],"INSUFFICIENT_SAMPLES")
    def test_invalid_quality_count_rejected(self):
        with self.assertRaises(ValueError):
            compare({},{"by_league":{"NBA":{"pairs":2,"quality_screen_passed_pairs":3}}})
    def test_never_verifies_opportunities(self):
        result=compare({}, {})
        self.assertFalse(result["trade_allowed"])
        self.assertEqual(result["verified_opportunities"],0)

if __name__=="__main__":
    unittest.main()
