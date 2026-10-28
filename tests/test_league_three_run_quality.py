import unittest
from league_three_run_quality import assess

def sample(n, passed):
    return {"by_league":{"NBA":{"pairs":n,"quality_screen_passed_pairs":passed}}}

class ThreeRunQualityTests(unittest.TestCase):
    def test_three_increasing_rates_with_minimum_samples(self):
        x=assess(sample(4,1),sample(4,2),sample(4,3))
        row=x["by_league"]["NBA"]
        self.assertTrue(row["minimum_samples_met"])
        self.assertTrue(row["three_run_improvement_observed"])
        self.assertEqual(row["pass_rates_pct_by_run"],[25.0,50.0,75.0])
        self.assertFalse(x["trade_allowed"])
    def test_small_samples_cannot_pass(self):
        x=assess(sample(2,0),sample(2,1),sample(2,2))
        self.assertEqual(x["by_league"]["NBA"]["status"],"INSUFFICIENT_SAMPLES")
    def test_missing_league_is_insufficient(self):
        x=assess({},sample(4,2),sample(4,3))
        self.assertFalse(x["by_league"]["NBA"]["three_run_improvement_observed"])
    def test_invalid_sample_counts(self):
        with self.assertRaises(ValueError):
            assess(sample(3,4),sample(3,1),sample(3,2))

if __name__=="__main__":
    unittest.main()
