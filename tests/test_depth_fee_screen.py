import unittest
from depth_fee_screen import screen
class DepthFeeTests(unittest.TestCase):
 def setUp(self):
  self.data={"rows":[{"kalshi_ticker":"K","observations":[
   {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.65","100"]],"yes_dollars":[]}}},
   {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.50","size":"100"}]}}]}]}
 def test_missing_rates_blocks(self):
  self.assertEqual(screen(self.data)["status"],"FEE_INPUTS_REQUIRED")
 def test_no_opposite_mapping_does_not_claim_candidates(self):
  r=screen(self.data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01")
  self.assertEqual(r["status"],"OPPOSING_OUTCOME_MAPPING_REQUIRED")
  self.assertEqual(r["rows"],[])
 def test_wrong_token_map_blocks(self):
  r=screen(self.data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",
      opposing_tokens={"K|YES":"999"})
  self.assertEqual(r["rows"],[])
 def test_positive_fee_adjusted_scenario_not_verified(self):
  r=screen(self.data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",opposing_tokens={"K|YES":"123"})
  self.assertTrue(r["rows"])
  self.assertFalse(r["net_profit_verified"])
  self.assertFalse(r["rows"][0]["opposite_outcome_verified"])
 def test_near_miss_visible_without_positive_claim(self):
  r=screen(self.data,poly_rate="0.2",kalshi_multiplier="4",extra_cost="4",
      opposing_tokens={"K|YES":"123"})
  self.assertEqual(r["rows"],[])
  self.assertTrue(r["near_misses"])
  self.assertLessEqual(float(r["near_misses"][0]["scenario"]["hypothetical_net_usd"]),0)
  self.assertFalse(r["net_profit_verified"])
  self.assertGreater(float(r["near_misses"][0]["scenario"]["minimum_total_cost_reduction_to_positive_usd"]),0)
 def test_costs_can_remove_positive_gross(self):
  r=screen(self.data,poly_rate="0.2",kalshi_multiplier="4",extra_cost="4",opposing_tokens={"K|YES":"123"})
  self.assertEqual(r["rows"],[])
if __name__=="__main__":unittest.main()
