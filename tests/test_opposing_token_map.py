import unittest
from opposing_token_map import make_mapping
def cand(team,title):
 return {"match_method":"sports_identifier_date_teams_research",
 "kalshi_ticker":"KXNBAGAME-26OCT28OKCDAL-"+team,"kalshi_title":title,
 "polymarket_id":"1","polymarket_slug":"nba-okc-dal-2026-10-28",
 "polymarket_outcomes":'["Thunder","Mavericks"]',
 "polymarket_clob_token_ids":'["123","456"]'}
class MapTests(unittest.TestCase):
 def test_two_clear_outcomes_select_opposite(self):
  r=make_mapping([cand("OKC","Will Thunder win?"),cand("DAL","Will Mavericks win?")])
  self.assertEqual(r["opposing_token_map"]["KXNBAGAME-26OCT28OKCDAL-OKC|YES"],"456")
  self.assertEqual(r["mapped_pairs"],2)
  self.assertFalse(r["market_rules_verified"])
 def test_missing_label_blocks(self):
  a=cand("OKC","Will Oklahoma City win?")
  self.assertEqual(make_mapping([a,cand("DAL","Will Dallas win?")])["mapped_pairs"],0)
 def test_single_team_blocks(self):
  self.assertEqual(make_mapping([cand("OKC","Thunder win")])["mapped_pairs"],0)
if __name__=="__main__":unittest.main()
