import unittest
from watchlist_trends import compare
class TrendTests(unittest.TestCase):
 def test_improving_and_missing(self):
  def make(value):
   return {"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"12","illustrative_net_usd":value}]}
  r=compare(make("-0.5"),make("-0.2"))
  self.assertEqual(r["changes"][0]["trend"],"IMPROVING")
  self.assertEqual(r["changes"][0]["change_usd"],"0.3")
  self.assertFalse(r["trade_allowed"])
  self.assertEqual(r["trend_counts"]["IMPROVING"],1)
  self.assertEqual(r["trend_counts"]["WORSENING"],0)
  self.assertEqual(compare({},make("-0.2"))["changes"][0]["trend"],"NEW")
if __name__=="__main__":unittest.main()
