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
 def test_invalid_inputs_rejected(self):
  with self.assertRaises(ValueError): rank({})
  self.assertEqual(rank({"near_misses":[]})["watchlist"],[])
if __name__=="__main__":unittest.main()
