import unittest
from sports_event_leads import group_leads
class Tests(unittest.TestCase):
 def test_groups_same_event_without_claiming_match(self):
  s={"candidates":[{"kalshi_ticker":"K1","polymarket_id":"P1"},{"kalshi_ticker":"K2","polymarket_id":"P1"}]}
  k={"markets":[{"ticker":"K1","event_ticker":"EV"},{"ticker":"K2","event_ticker":"EV"}]}
  p={"markets":[{"id":"P1","slug":"game-a"}]}
  result=group_leads(s,k,p)
  self.assertEqual(result["groups_found"],1)
  self.assertEqual(result["event_groups"][0]["kalshi_tickers"],["K1","K2"])
  self.assertFalse(result["event_groups"][0]["event_identity_verified"])
 def test_missing_identifiers_skipped(self):
  r=group_leads({"candidates":[{"kalshi_ticker":"K","polymarket_id":"P"}]},
    {"markets":[{"ticker":"K"}]},{"markets":[{"id":"P"}]})
  self.assertEqual(r["groups_found"],0)
  self.assertEqual(r["skipped_missing_identifiers"],1)
if __name__=="__main__": unittest.main()
