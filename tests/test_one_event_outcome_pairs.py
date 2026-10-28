import unittest
from one_event_outcome_pairs import pair_game_winners
class OutcomePairTests(unittest.TestCase):
    def test_distinct_outcomes_with_actual_labels(self):
        k={"markets":[{"ticker":"KXNBAGAME-26OCT28OKCDAL-OKC","title":"Oklahoma City Thunder wins"},
                      {"ticker":"KXNBAGAME-26OCT28OKCDAL-DAL","title":"Dallas Mavericks wins"}]}
        p={"markets":[{"id":"m","question":"Thunder vs. Mavericks",
          "outcomes":'["Thunder","Mavericks"]',"clobTokenIds":'["100","200"]'}]}
        pairs=pair_game_winners(k,p)
        self.assertEqual({x["team"] for x in pairs},{"OKC","DAL"})
        self.assertEqual({x["polymarket_token_id"] for x in pairs},{"100","200"})
        self.assertTrue(all(not x["market_rules_verified"] for x in pairs))
    def test_rejects_other_event_and_props(self):
        k={"markets":[{"ticker":"KXNBAGAME-26OCT29OKCDAL-OKC","title":"Oklahoma City Thunder wins"}]}
        p={"markets":[{"question":"First to score","outcomes":'["Thunder","Mavericks"]',"clobTokenIds":'["1","2"]'}]}
        self.assertEqual(pair_game_winners(k,p),[])
    def test_rejects_missing_outcomes(self):
        self.assertEqual(pair_game_winners({"markets":[]},{"markets":[{"question":"Thunder vs. Mavericks"}]}),[])
if __name__=="__main__": unittest.main()
