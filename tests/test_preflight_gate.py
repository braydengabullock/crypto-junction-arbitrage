import unittest
from preflight_gate import assess
def payload():
    m={"research_only":True,"candidates_returned":1}
    b={"research_only":True,"candidate_count":1,
       "rows":[{"executable_opportunity_verified":False}]}
    q={"research_only":True,"rows_examined":1,
       "rows_with_synchronized_observations":1,
       "rows_with_displayed_depth_on_both_venues":1}
    r={"research_only":True,"verified_trade_opportunities":0,
       "actual_profit_usd":None}
    return m,b,q,r
class PreflightTests(unittest.TestCase):
    def test_good_collection_does_not_mean_backtest_ready(self):
        r=assess(*payload())
        self.assertTrue(r["observation_usable"])
        self.assertFalse(r["data_sufficient_for_paper_backtest"])
    def test_missing_data_detected(self):
        m,b,q,r=payload(); q["rows_with_synchronized_observations"]=0
        self.assertFalse(assess(m,b,q,r)["observation_usable"])
    def test_forged_profit_claim_rejected(self):
        m,b,q,r=payload();r["actual_profit_usd"]="100"
        self.assertFalse(assess(m,b,q,r)["observation_usable"])
    def test_empty_candidates_not_success(self):
        m,b,q,r=payload()
        m["candidates_returned"]=0
        b["candidate_count"]=0;b["rows"]=[]
        q["rows_examined"]=0
        self.assertFalse(assess(m,b,q,r)["observation_usable"])
if __name__=="__main__":
    unittest.main()
