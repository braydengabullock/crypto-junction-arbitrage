import unittest
from market_comparison import sports_identifier_match,compare,tokenize
class SportsIdentifierTests(unittest.TestCase):
 def test_matching_game_without_title_similarity(self):
  k={"ticker":"KXNBAGAME-26OCT28OKCDAL-OKC","title":"Oklahoma City Thunder"}
  p={"id":"P","slug":"nba-okc-dal-2026-10-28","question":"Thunder vs. Mavericks",
      "enableOrderBook":True,"acceptingOrders":True}
  self.assertTrue(sports_identifier_match(k,p))
  results,count=compare({"markets":[k]},{"markets":[p]})
  self.assertEqual(count,1)
  self.assertEqual(results[0]["match_method"],"sports_identifier_date_teams_research")
  self.assertFalse(results[0]["market_rules_verified"])
 def test_real_game_ranked_above_false_final_match(self):
  k={"ticker":"KXNBAGAME-26OCT28SASUTA-SAS","title":"San Antonio wins"}
  real={"id":"GAME","slug":"nba-sas-uta-2026-10-28","question":"Spurs vs Jazz","enableOrderBook":True}
  false={"id":"FINAL","slug":"will-san-antonio-spurs-win-2027-finals",
         "question":"Will San Antonio win the NBA Finals?","enableOrderBook":True}
  matches,_=compare({"markets":[k]},{"markets":[false,real]})
  self.assertEqual(matches[0]["polymarket_id"],"GAME")
  self.assertEqual(matches[0]["match_method"],"sports_identifier_date_teams_research")
 def test_date_or_team_mismatch_does_not_match(self):
  k={"ticker":"KXNBAGAME-26OCT28OKCDAL-OKC"}
  for slug in ("nba-okc-dal-2026-10-29","nba-okc-lal-2026-10-28","nfl-okc-dal-2026-10-28"):
   self.assertFalse(sports_identifier_match(k,{"slug":slug}))
 def test_reversed_team_slug(self):
  self.assertTrue(sports_identifier_match(
    {"ticker":"KXNBAGAME-26OCT28OKCDAL-DAL"},
    {"slug":"nba-dal-okc-2026-10-28"}))
 def test_alias_expands_with_word_boundaries(self):
  self.assertEqual(tokenize("LA vs NY"),{"los","angeles","new","york"})
 def test_compound_excluded(self):
  k={"ticker":"KXCROSSCATEGORY-26OCT28OKCDAL-OKC","title":"NBA"}
  self.assertFalse(sports_identifier_match(k,{"slug":"nba-okc-dal-2026-10-28"}))
if __name__=="__main__": unittest.main()
