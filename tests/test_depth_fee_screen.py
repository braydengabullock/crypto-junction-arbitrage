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
 def test_budget_up_to_5000_and_larger_book_depth(self):
  data={"rows":[{"kalshi_ticker":"LARGE","observations":[
    {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.65","2000"]],"yes_dollars":[]}}},
    {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.50","size":"2000"}]}}]}]}
  result=screen(data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",
                budget="5000",opposing_tokens={"LARGE|YES":"123"})
  self.assertEqual(result["max_combined_research_budget_usd"],"5000")
  self.assertGreater(result["rows"][0]["scenario"]["contracts_each"],100)
  self.assertLessEqual(Decimal(result["rows"][0]["scenario"]["total_cost_usd"]),Decimal("5000"))
  self.assertFalse(result["trade_allowed"])
  with self.assertRaises(ValueError):
   screen(data,poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.01",
          budget="5000.01",opposing_tokens={"LARGE|YES":"123"})
 def test_roi_and_dollar_profit_optima_can_differ(self):
  data={"rows":[{"kalshi_ticker":"SIZED","observations":[
    {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.75","20"],["0.65","80"]],"yes_dollars":[]}}},
    {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.50","size":"100"}]}}]}]}
  result=screen(data,poly_rate="0",kalshi_multiplier="0",extra_cost="0",
                budget="5000",opposing_tokens={"SIZED|YES":"123"})
  item=result["rows"][0]
  self.assertEqual(item["scenario"]["contracts_each"],100)
  self.assertEqual(item["max_roi_scenario"]["contracts_each"],20)
  self.assertTrue(item["sizing_comparison"]["different_optimal_quantities"])
  self.assertGreater(Decimal(item["max_roi_scenario"]["hypothetical_roi_pct"]),
                     Decimal(item["scenario"]["hypothetical_roi_pct"]))
  self.assertFalse(result["trade_allowed"])
 def test_per_venue_limit_bounds_size_even_with_combined_headroom(self):
  data={"rows":[{"kalshi_ticker":"UNBALANCED","observations":[
    {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.10","5000"]],"yes_dollars":[]}}},
    {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.05","size":"5000"}]}}]}]}
  r=screen(data,poly_rate="0",kalshi_multiplier="0",extra_cost="0",
           budget="5000",per_venue_budget="2500",
           opposing_tokens={"UNBALANCED|YES":"123"})
  self.assertEqual(r["max_per_venue_research_budget_usd"],"2500")
  scenario=r["rows"][0]["scenario"]
  self.assertLessEqual(Decimal(scenario["venue_allocation"]["kalshi_with_modeled_fee_usd"]),Decimal("2500"))
  self.assertLessEqual(Decimal(scenario["venue_allocation"]["polymarket_with_modeled_fee_usd"]),Decimal("2500"))
  self.assertLess(Decimal(scenario["total_cost_usd"]),Decimal("5000"))
  self.assertFalse(r["trade_allowed"])
  with self.assertRaises(ValueError):
   screen(data,poly_rate="0",kalshi_multiplier="0",extra_cost="0",
          per_venue_budget="2500.01",opposing_tokens={"UNBALANCED|YES":"123"})
 def test_unassigned_fx_and_overhead_reserve_each_venue(self):
  data={"rows":[{"kalshi_ticker":"OVERHEAD","observations":[
    {"venue":"kalshi","book":{"orderbook_fp":{"no_dollars":[["0.5","6000"]],"yes_dollars":[]}}},
    {"venue":"polymarket","token_id":"123","book":{"asks":[{"price":"0.4","size":"6000"}]}}]}]}
  result=screen(data,poly_rate="0",kalshi_multiplier="0",extra_cost="100",
                fx_cost="100",budget="5000",per_venue_budget="2500",
                opposing_tokens={"OVERHEAD|YES":"123"})
  scenario=result["near_misses"][0]["scenario"]
  alloc=scenario["venue_allocation"]
  self.assertTrue(alloc["overhead_funding_venue_unverified"])
  self.assertLessEqual(Decimal(alloc["kalshi_conservative_funding_reserve_usd"]),Decimal("2500"))
  self.assertLessEqual(Decimal(alloc["polymarket_conservative_funding_reserve_usd"]),Decimal("2500"))
  self.assertEqual(Decimal(alloc["kalshi_conservative_funding_reserve_usd"]) -
                   Decimal(alloc["kalshi_with_modeled_fee_usd"]),Decimal("200"))
  self.assertFalse(result["trade_allowed"])
 def test_explicit_overhead_funding_assignments(self):
  kwargs=dict(poly_rate="0",kalshi_multiplier="0",extra_cost="3",fx_cost="2",
              opposing_tokens={"K|YES":"123"})
  unknown=screen(self.data,**kwargs)["near_misses"][0]["scenario"]["venue_allocation"]
  assigned=screen(self.data,extra_cost_venue="kalshi",fx_cost_venue="external",
                  **kwargs)["near_misses"][0]["scenario"]["venue_allocation"]
  self.assertTrue(unknown["overhead_funding_venue_unverified"])
  self.assertFalse(assigned["overhead_funding_venue_unverified"])
  self.assertEqual(Decimal(unknown["kalshi_conservative_funding_reserve_usd"]) -
                   Decimal(assigned["kalshi_conservative_funding_reserve_usd"]),Decimal("2"))
  self.assertEqual(Decimal(unknown["polymarket_conservative_funding_reserve_usd"]) -
                   Decimal(assigned["polymarket_conservative_funding_reserve_usd"]),Decimal("5"))
  with self.assertRaises(ValueError):
   screen(self.data,extra_cost_venue="invalid",**kwargs)
  unknown_scenario=screen(self.data,**kwargs)["near_misses"][0]["fixed_ten_contract_pairs"]
  assigned_scenario=screen(self.data,extra_cost_venue="kalshi",fx_cost_venue="external",
                            **kwargs)["near_misses"][0]["fixed_ten_contract_pairs"]
  self.assertEqual(unknown_scenario["total_cost_usd"],assigned_scenario["total_cost_usd"])
  self.assertEqual(unknown_scenario["hypothetical_net_usd"],assigned_scenario["hypothetical_net_usd"])
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
