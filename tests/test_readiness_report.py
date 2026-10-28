import unittest
from readiness_report import readiness

class ReadinessTests(unittest.TestCase):
    def test_title_match_does_not_count_as_profit(self):
        k={"markets":[{"ticker":"K","title":"Will Bitcoin exceed 100000 in 2027?"}]}
        p={"markets":[{"id":"P","question":"Will Bitcoin exceed 100000 in 2027?"}]}
        report=readiness(k,p)
        self.assertEqual(report["title_match_candidates"],1)
        self.assertEqual(report["validated_executable_opportunities"],0)
        self.assertFalse(report["backtest_ready"])
        self.assertIsNone(report["actual_realized_profit_usd"])
    def test_empty_market_snapshots(self):
        report=readiness({"markets":[]},{"markets":[]})
        self.assertEqual(report["title_match_candidates"],0)
        self.assertFalse(report["backtest_ready"])
if __name__=="__main__":
    unittest.main()
