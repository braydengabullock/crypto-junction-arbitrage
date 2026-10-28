import unittest
from near_miss_watchlist import rank
class RankTests(unittest.TestCase):
 def test_ranks_closest_gap_first(self):
  def row(ticker,gain):
   return {"kalshi_ticker":ticker,"kalshi_side":"YES","polymarket_token_id":"123",
      "scenario":{"hypothetical_net_usd":gain,"total_cost_usd":"99","contracts_each":100}}
  r=rank({"near_misses":[row("B","-0.7"),row("A","-0.1")]})
  self.assertEqual(r["watchlist"][0]["kalshi_ticker"],"A")
  self.assertFalse(r["trade_allowed"])
 def test_fixed_ten_profit_gap(self):
  item={"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"123",
    "scenario":{"hypothetical_net_usd":"-0.2","total_cost_usd":"10.2","contracts_each":10},
    "fixed_ten_contract_pairs":{"contracts_each":10,"hypothetical_net_usd":"-0.2"}}
  result=rank({"near_misses":[item]})
  self.assertEqual(result["watchlist"][0]["fixed_ten_gap_to_one_cent_usd"],"0.21")
 def test_positive_projection_with_missing_fx_remains_incomplete(self):
  item={"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"123",
        "scenario":{"hypothetical_net_usd":"0.05","total_cost_usd":"9.95",
                    "contracts_each":10,"net_roi_tier":"HIGHER_PRIORITY_0_5_PLUS",
                    "venue_allocation":{"kalshi_displayed_usd":"4",
                        "polymarket_displayed_usd":"5","modeled_fees_and_extra_usd":"0.95",
                        "assumed_fx_cost_usd":"0"}}}
  no_fx=rank({"near_misses":[item],"fx_cost_supplied":False})
  self.assertEqual(no_fx["positive_but_cost_incomplete_count"],1)
  self.assertEqual(no_fx["watchlist"][0]["cost_evidence_status"],"INCOMPLETE_COST_INPUTS")
  with_fx=rank({"near_misses":[item],"fx_cost_supplied":True})
  self.assertEqual(with_fx["cost_inputs_complete_for_model_count"],1)
  self.assertEqual(with_fx["watchlist"][0]["cost_evidence_status"],"MODELED_COST_INPUTS_PRESENT_UNVERIFIED")
  self.assertFalse(with_fx["trade_allowed"])
 def test_invalid_inputs_rejected(self):
  with self.assertRaises(ValueError): rank({})
  self.assertEqual(rank({"near_misses":[]})["watchlist"],[])
if __name__=="__main__":unittest.main()
