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
 def test_changed_quantity_not_claimed_as_price_trend(self):
  old={"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":"-1","contracts_each":10}]}
  new={"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":"-0.5","contracts_each":5}]}
  r=compare(old,new)
  self.assertEqual(r["changes"][0]["trend"],"SIZE_CHANGED_NOT_COMPARABLE")
  self.assertIsNone(r["changes"][0]["change_usd"])
if __name__=="__main__":unittest.main()
