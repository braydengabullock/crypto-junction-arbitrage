import sqlite3
import unittest
from datetime import datetime,timezone
from paper_journal import connect, record, settle, report

class JournalTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        self.pair={"capital_usd":"99.75","total_cost":"99.75",
                   "estimated_net_usd":"5.25"}
        self.review={"status":"PAPER_REVIEW","pair":self.pair}
        self.candidate={"source_a":"Kalshi","source_b":"ForecastEx"}
        self.time="2026-10-27T18:00:00+00:00"
    def tearDown(self):
        self.db.close()
    def entry(self):
        return record(self.db,"CJ-ARB-001",self.candidate,self.review,self.time)
    def test_entry_is_not_actual_fill(self):
        out=self.entry()
        self.assertEqual(out["fill_status"],"HYPOTHETICAL_ONLY")
        self.assertIsNone(report(self.db)[0]["settlement"])
    def test_consistent_settlement(self):
        self.entry()
        out=settle(self.db,"CJ-ARB-001",observed_at="2026-10-27T19:30:00+00:00",
                   payout_a="105",payout_b="0",source_a="mock_a",source_b="mock_b")
        self.assertTrue(out["settlement_consistent_with_model"])
        self.assertEqual(out["realized_hypothetical_profit_usd"],"5.25")
    def test_inconsistent_settlement(self):
        self.entry()
        out=settle(self.db,"CJ-ARB-001",observed_at="2026-10-27T19:30:00+00:00",
                   payout_a="0",payout_b="0",source_a="mock_a",source_b="mock_b")
        self.assertFalse(out["settlement_consistent_with_model"])
        self.assertEqual(out["realized_hypothetical_profit_usd"],"-99.75")
    def test_duplicate_entry_rejected(self):
        self.entry()
        with self.assertRaises(sqlite3.IntegrityError):
            self.entry()
    def test_repeat_settlement_rejected(self):
        self.entry()
        kwargs=dict(observed_at="2026-10-27T19:30:00+00:00",
                   payout_a="105",payout_b="0",source_a="mock_a",source_b="mock_b")
        settle(self.db,"CJ-ARB-001",**kwargs)
        with self.assertRaises(ValueError):
            settle(self.db,"CJ-ARB-001",**kwargs)
    def test_settlement_before_entry_rejected(self):
        self.entry()
        with self.assertRaises(ValueError):
            settle(self.db,"CJ-ARB-001",observed_at="2026-10-27T17:00:00+00:00",
                   payout_a="105",payout_b="0",source_a="mock_a",source_b="mock_b")
    def test_non_passing_entry_rejected(self):
        with self.assertRaises(ValueError):
            record(self.db,"bad",{},{"status":"BLOCKED"},self.time)

if __name__=="__main__":
    unittest.main()
