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
  r=make_mapping([cand("OKC","Oklahoma City wins"),cand("DAL","Dallas wins")])
  self.assertEqual(r["opposing_token_map"]["KXNBAGAME-26OCT28OKCDAL-OKC|YES"],"456")
  self.assertEqual(r["mapped_pairs"],2)
  self.assertFalse(r["market_rules_verified"])
 def test_nhl_two_team_outcomes(self):
  a=cand("TOR","Toronto wins")
  b=cand("MTL","Montreal wins")
  for item,code in ((a,"TOR"),(b,"MTL")):
   item["kalshi_ticker"]="KXNHLGAME-26OCT28TORMTL-"+code
   item["polymarket_slug"]="nhl-tor-mtl-2026-10-28"
   item["polymarket_outcomes"]='["Maple Leafs","Canadiens"]'
  result=make_mapping([a,b])
  self.assertEqual(result["mapped_pairs"],2)
  self.assertEqual(result["opposing_token_map"]["KXNHLGAME-26OCT28TORMTL-TOR|YES"],"456")
  self.assertFalse(result["market_rules_verified"])
 def test_nhl_unknown_outcome_rejected(self):
  a=cand("TOR","Toronto wins")
  b=cand("MTL","Montreal wins")
  for item,code in ((a,"TOR"),(b,"MTL")):
   item["kalshi_ticker"]="KXNHLGAME-26OCT28TORMTL-"+code
   item["polymarket_outcomes"]='["Maple Leafs","Unknown"]'
  self.assertEqual(make_mapping([a,b])["mapped_pairs"],0)
 def test_missing_label_blocks(self):
  a=cand("OKC","Unknown city wins")
  self.assertEqual(make_mapping([a,cand("DAL","Will Dallas win?")])["mapped_pairs"],0)
 def test_unrecognized_label_blocks(self):
  a=cand("OKC","Oklahoma City wins")
  a["polymarket_outcomes"]='["Thunder","Unrecognized"]'
  self.assertEqual(make_mapping([a,cand("DAL","Dallas wins")])["mapped_pairs"],0)
 def test_single_team_blocks(self):
  self.assertEqual(make_mapping([cand("OKC","Thunder win")])["mapped_pairs"],0)
if __name__=="__main__":unittest.main()
