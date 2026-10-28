import unittest
from watchlist_trends import compare
class TrendTests(unittest.TestCase):
 def test_improving_and_missing(self):
  def make(value):
   return {"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":value,"contracts_each":10}]}
  r=compare(make("-0.5"),make("-0.2"))
  self.assertEqual(r["changes"][0]["trend"],"IMPROVING")
  self.assertEqual(r["changes"][0]["change_usd"],"0.3")
  self.assertFalse(r["trade_allowed"])
  self.assertEqual(r["trend_counts"]["IMPROVING"],1)
  self.assertEqual(r["trend_counts"]["WORSENING"],0)
  self.assertEqual(compare({},make("-0.2"))["changes"][0]["trend"],"NEW")
 def test_fixed_ten_benchmark_survives_size_change(self):
  def row(n,net,fixed):
   return {"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12",
           "illustrative_net_usd":net,"contracts_each":n,
           "fixed_ten_contract_pairs":{"contracts_each":10,"hypothetical_net_usd":fixed}}
  result=compare({"watchlist":[row(30,"-1.0","-0.5")]},
                 {"watchlist":[row(25,"-0.8","-0.3")]})
  change=result["changes"][0]
  self.assertEqual(change["trend"],"SIZE_CHANGED_NOT_COMPARABLE")
  self.assertEqual(change["fixed_ten_trend"],"IMPROVING")
  self.assertEqual(change["fixed_ten_change_usd"],"0.2")
  self.assertEqual(result["fixed_ten_trend_counts"]["IMPROVING"],1)
 def test_approaching_break_even_requires_improvement(self):
  def row(value):
   return {"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12",
     "illustrative_net_usd":value,"contracts_each":10,
     "fixed_ten_contract_pairs":{"contracts_each":10,"hypothetical_net_usd":value}}
  improving=compare({"watchlist":[dict(row("-0.30"),quote_quality={"both_books_present":True,"within_20_seconds":True,"sufficient_depth_for_ten":True})]},{"watchlist":[dict(row("-0.20"),quote_quality={"both_books_present":True,"within_20_seconds":True,"sufficient_depth_for_ten":True})]})
  self.assertEqual(improving["monitoring_priority_counts"]["APPROACHING_BREAK_EVEN"],1)
  worsening=compare({"watchlist":[row("-0.10")]},{"watchlist":[row("-0.20")]})
  self.assertEqual(worsening["monitoring_priority_counts"]["APPROACHING_BREAK_EVEN"],0)
 def test_quote_quality_fail_closed(self):
  def row(quality):
   return {"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12",
           "illustrative_net_usd":"-0.2","contracts_each":10,
           "fixed_ten_contract_pairs":{"contracts_each":10,"hypothetical_net_usd":"-0.2"},
           "quote_quality":quality}
  bad=compare({"watchlist":[row({})]},{"watchlist":[row({})]})
  self.assertFalse(bad["changes"][0]["quote_quality_passed"])
  self.assertEqual(bad["changes"][0]["monitoring_priority"],"MONITOR_ONLY")
  good={"both_books_present":True,"within_20_seconds":True,"sufficient_depth_for_ten":True}
  result=compare({"watchlist":[row(good)]},{"watchlist":[row(good)]})
  self.assertTrue(result["changes"][0]["quote_quality_passed"])
 def test_changed_quantity_not_claimed_as_price_trend(self):
  old={"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":"-1","contracts_each":10}]}
  new={"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":"-0.5","contracts_each":5}]}
  r=compare(old,new)
  self.assertEqual(r["changes"][0]["trend"],"SIZE_CHANGED_NOT_COMPARABLE")
  self.assertIsNone(r["changes"][0]["change_usd"])
if __name__=="__main__":unittest.main()
