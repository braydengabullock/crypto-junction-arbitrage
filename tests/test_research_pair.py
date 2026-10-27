import unittest
from datetime import datetime, timezone, timedelta
from research_pair import assess_pair, format_research_alert

NOW = datetime(2026,10,27,18,0,tzinfo=timezone.utc)
def sample():
    stamp=lambda t:t.isoformat()
    return dict(source_a="Kalshi",source_b="ForecastEx",contract_a="AAA",
      contract_b="BBB",side_a="YES",side_b="NO",ask_a="0.40",
      ask_b="0.53",fee_a="0.01",fee_b="0.01",depth_a=500,depth_b=500,
      asof_a=stamp(NOW-timedelta(seconds=2)),asof_b=stamp(NOW-timedelta(seconds=3)),
      expected_payout_a=stamp(NOW+timedelta(minutes=75)),
      expected_payout_b=stamp(NOW+timedelta(minutes=80)),
      settlement_verified=True,eligibility_verified=True,
      currency_a="USD",currency_b="USD",
      url_a="https://example.com/a",url_b="https://example.com/b")

class ResearchPairTests(unittest.TestCase):
    def test_sizing_and_research_message(self):
        a=sample(); result=assess_pair(a,now=NOW)
        self.assertEqual(result["status"],"RESEARCH_REVIEW")
        self.assertEqual(result["contracts_each"],105)
        self.assertEqual(result["capital_usd"],"99.75")
        self.assertEqual(result["estimated_net_usd"],"5.25")
        self.assertIn("NOT A TRADE SIGNAL",format_research_alert(a,result))
    def test_block_rule_match(self):
        p=sample();p["settlement_verified"]=False
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_block_account_access(self):
        p=sample();p["eligibility_verified"]=False
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_block_stale_quote(self):
        p=sample();p["asof_b"]=(NOW-timedelta(minutes=4)).isoformat()
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_block_long_settlement(self):
        p=sample();p["expected_payout_b"]=(NOW+timedelta(hours=4)).isoformat()
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_block_low_roi(self):
        p=sample();p["ask_b"]="0.59"
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_block_insufficient_depth(self):
        p=sample();p["depth_a"]=0
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")
    def test_no_alert_for_blocked(self):
        p=sample();p["settlement_verified"]=False
        self.assertIsNone(format_research_alert(p,assess_pair(p,now=NOW)))
    def test_missing_field_is_blocked(self):
        p=sample();del p["fee_b"]
        self.assertEqual(assess_pair(p,now=NOW)["status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
