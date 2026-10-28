import unittest
from depth_fee_screen import screen,roi_tier
from decimal import Decimal
class DepthFeeTests(unittest.TestCase):
 def setUp(self):
  self.data={"rows":[{"kalshi_ticker":"K","observations":[
   {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.65","100"]],"yes_dollars":[]}}},
   {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.50","size":"100"}]}}]}]}
 def test_revised_profit_tiers(self):
  self.assertEqual(roi_tier(Decimal("0"),Decimal("100")),"NONPOSITIVE_REJECT")
  self.assertEqual(roi_tier(Decimal("-0.01"),Decimal("100")),"NONPOSITIVE_REJECT")
  self.assertEqual(roi_tier(Decimal("0.01"),Decimal("100")),"SMALL_POSITIVE")
  self.assertEqual(roi_tier(Decimal("0.50"),Decimal("100")),"HIGHER_PRIORITY_0_5_PLUS")
  self.assertEqual(roi_tier(Decimal("2.00"),Decimal("100")),"EXCEPTIONAL_2_PLUS")
 def test_fx_cost_reduces_projected_profit_and_is_disclosed(self):
  kwargs=dict(poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",
              opposing_tokens={"K|YES":"123"})
  no_fx=screen(self.data,**kwargs)
  with_fx=screen(self.data,fx_cost="0.20",**kwargs)
  self.assertTrue(with_fx["fx_cost_supplied"])
  self.assertFalse(no_fx["fx_cost_supplied"])
  self.assertEqual(Decimal(with_fx["fx_cost_assumed_usd"]),Decimal("0.20"))
  self.assertEqual(Decimal(with_fx["near_misses"][0]["fixed_ten_contract_pairs"]["hypothetical_net_usd"]),
                   Decimal(no_fx["near_misses"][0]["fixed_ten_contract_pairs"]["hypothetical_net_usd"])-Decimal("0.20"))
  self.assertFalse(with_fx["net_profit_verified"])
 def test_fx_cost_must_be_nonnegative(self):
  with self.assertRaises(ValueError):
   screen(self.data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",
          fx_cost="-0.01",opposing_tokens={"K|YES":"123"})
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
  self.assertIn("venue_allocation",r["rows"][0]["scenario"])
  self.assertLessEqual(Decimal(r["rows"][0]["scenario"]["total_cost_usd"]),Decimal("100"))
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
