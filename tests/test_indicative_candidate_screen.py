import unittest
from indicative_candidate_screen import screen
class ScreenTests(unittest.TestCase):
    def test_indicative_outcomes_not_claimed_as_pairs(self):
        matches={"candidates":[{"kalshi_ticker":"K1","kalshi_title":"Game",
                  "polymarket_id":"p","title_similarity":0.9}]}
        poly={"markets":[{"id":"p","question":"Game",
             "outcomes":'["A","B"]',"outcomePrices":'["0.65","0.35"]'}]}
        r=screen(matches,poly)
        self.assertEqual(r["candidate_outcomes"],2)
        self.assertFalse(r["rows"][0]["opposing_outcome_verified"])
        self.assertFalse(r["rows"][0]["net_roi_verified"])
    def test_bad_prices_rejected(self):
        r=screen({"candidates":[{"polymarket_id":"p"}]},
                 {"markets":[{"id":"p","outcomes":'["A","B"]',
                  "outcomePrices":'["Infinity","-1"]'}]})
        self.assertEqual(r["candidate_outcomes"],0)
if __name__=="__main__":unittest.main()
