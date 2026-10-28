import unittest
from sustained_watchlist import sustained
def snap(v):
 return {"watchlist":[{"kalshi_ticker":"K","kalshi_side":"YES","polymarket_token_id":"123",
 "fixed_ten_contract_pairs":{"contracts_each":10,"hypothetical_net_usd":str(v)}}]}
class TestSustained(unittest.TestCase):
 def test_two_improvements(self):
  r=sustained(snap("-1"),snap("-.5"),snap("-.1"))
  self.assertEqual(r["sustained_improvements"],1)
  self.assertFalse(r["trade_allowed"])
 def test_one_reversal(self):
  self.assertEqual(sustained(snap("-1"),snap("-.5"),snap("-.6"))["sustained_improvements"],0)
 def test_missing_snapshot(self):
  self.assertEqual(sustained({},snap("-.5"),snap("-.1"))["three_run_comparisons"],0)
if __name__=="__main__":unittest.main()
