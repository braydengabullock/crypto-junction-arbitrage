import unittest
from datetime import datetime, timedelta, timezone
from paper_review import review

NOW = datetime(2026, 10, 27, 18, 0, tzinfo=timezone.utc)
def example():
    iso=lambda t:t.isoformat()
    return dict(source_a="Kalshi",source_b="ForecastEx",contract_a="DEMO_A",
        contract_b="DEMO_B",side_a="YES",side_b="NO",ask_a="0.40",ask_b="0.53",
        fee_a="0.01",fee_b="0.01",depth_a=500,depth_b=500,
        asof_a=iso(NOW-timedelta(seconds=2)),asof_b=iso(NOW-timedelta(seconds=2)),
        expected_payout_a=iso(NOW+timedelta(minutes=75)),
        expected_payout_b=iso(NOW+timedelta(minutes=80)),
        settlement_verified=True,eligibility_verified=True,
        currency_a="USD",currency_b="USD",
        url_a="https://example.com/a",url_b="https://example.com/b")
def balances():
    return dict(balance_a=200,balance_b=200,portfolio_total=1000,total_current_committed=0)

class PipelineTests(unittest.TestCase):
    def test_complete_offline_review(self):
        r=review(example(),balances(),now=NOW)
        self.assertEqual(r["status"],"PAPER_REVIEW")
        self.assertEqual(r["pair"]["contracts_each"],105)
        self.assertIn("NOT A TRADE SIGNAL",r["message_preview"])
    def test_pair_fails_closed(self):
        p=example();p["settlement_verified"]=False
        r=review(p,balances(),now=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertNotIn("message_preview",r)
    def test_capital_fails_closed(self):
        b=balances();b["balance_a"]=20
        r=review(example(),b,now=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertNotIn("message_preview",r)
    def test_missing_balances_fail_closed(self):
        r=review(example(),{"balance_a":200},now=NOW)
        self.assertEqual(r["status"],"BLOCKED")
        self.assertNotIn("message_preview",r)
    def test_exposure_fails_closed(self):
        b=balances();b["total_current_committed"]=950
        self.assertEqual(review(example(),b,now=NOW)["status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
