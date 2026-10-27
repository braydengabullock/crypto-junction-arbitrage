import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scanner import evaluate, telegram_text

CFG = dict(budget_usd=100, min_net_roi_pct=2, max_payout_hours=2,
           max_quote_age_seconds=20, max_clock_skew_seconds=5)

def example(now=None):
    now = now or datetime.now(timezone.utc)
    iso = lambda d: d.isoformat()
    return dict(event="TEST EVENT", a_venue="A", a_contract="A1", a_side="YES",
                a_ask="0.40", a_depth="1000", a_fee_per_contract="0.01",
                a_market_url="https://example.com/a", b_venue="B", b_contract="B1",
                b_side="NO", b_ask="0.53", b_depth="1000",
                b_fee_per_contract="0.01", b_market_url="https://example.com/b",
                observed_at=iso(now - timedelta(seconds=3)),
                event_end_at=iso(now + timedelta(minutes=30)),
                expected_payout_at=iso(now + timedelta(minutes=75)),
                match_verified="true")

class EvaluationTests(unittest.TestCase):
    def test_pair_sizing_and_profit(self):
        now = datetime(2026, 10, 27, tzinfo=timezone.utc)
        result = evaluate(example(now), CFG, now)
        self.assertEqual(result["status"], "RESEARCH_PASS")
        self.assertEqual(result["contracts_each"], 105)
        self.assertAlmostEqual(result["total_cost"], 99.75)
        self.assertAlmostEqual(result["estimated_net_profit"], 5.25)
        self.assertIn("NOT A TRADE SIGNAL", telegram_text(result))
    def test_reject_unverified(self):
        now = datetime.now(timezone.utc)
        row = example(now); row["match_verified"] = "false"
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")
    def test_reject_stale(self):
        now = datetime.now(timezone.utc)
        row = example(now); row["observed_at"] = (now-timedelta(minutes=5)).isoformat()
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")
    def test_reject_low_roi(self):
        now = datetime.now(timezone.utc)
        row = example(now); row["b_ask"] = "0.58"
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")
    def test_reject_outside_settlement_window(self):
        now = datetime.now(timezone.utc)
        row = example(now); row["expected_payout_at"] = (now+timedelta(hours=3)).isoformat()
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")
    def test_reject_same_direction(self):
        now = datetime.now(timezone.utc)
        row = example(now); row["b_side"] = "YES"
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")
    def test_reject_missing_field(self):
        now = datetime.now(timezone.utc)
        row = example(now); del row["a_ask"]
        self.assertEqual(evaluate(row, CFG, now)["status"], "REJECT")

if __name__ == "__main__":
    unittest.main()
