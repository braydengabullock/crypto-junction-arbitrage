import unittest
from fee_estimates import kalshi_general_taker_fee,polymarket_sports_taker_fee,cost_screen
class FeeEstimateTests(unittest.TestCase):
 def test_general_fee_rounded_up_cents(self):
  self.assertEqual(str(kalshi_general_taker_fee(100,"0.50")),"1.75")
 def test_sports_fee_explicit(self):
  self.assertEqual(str(polymarket_sports_taker_fee(100,"0.50",rate="0.05")),"1.25000")
 def test_missing_market_rate_blocks(self):
  self.assertEqual(cost_screen(contracts=10,kalshi_price=".4",polymarket_price=".55",
       extra_cost="0",kalshi_multiplier="1")["status"],"FEE_INPUTS_REQUIRED")
 def test_positive_gross_can_be_negative_after_fees(self):
  r=cost_screen(contracts=10,kalshi_price=".45",polymarket_price=".54",
      poly_rate=".05",kalshi_multiplier="1",extra_cost=".02")
  self.assertFalse(r["hypothetical_positive_after_supplied_costs"])
  self.assertFalse(r["positive_net_verified"])
if __name__=="__main__":unittest.main()
