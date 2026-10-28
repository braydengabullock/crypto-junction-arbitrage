import unittest
from sports_candidate_shortlist import shortlist
class ShortlistTests(unittest.TestCase):
    def test_sports_only_deduplicated(self):
        a={"kalshi_ticker":"K","polymarket_id":"P","kalshi_title":"NBA game",
           "polymarket_question":"NBA basketball","title_similarity":0.8,
           "sports_candidate":True}
        b={"kalshi_ticker":"K2","polymarket_id":"P2","kalshi_title":"Election",
           "polymarket_question":"Election","title_similarity":0.9,
           "sports_candidate":False}
        r=shortlist({"candidates":[b,a,a]})
        self.assertEqual(r["sports_candidates_returned"],1)
        self.assertFalse(r["candidates"][0]["net_roi_verified"])
    def test_rejects_parlay_and_crosscategory_false_pairs(self):
        a={"kalshi_ticker":"KXCROSSCATEGORY-FOO","polymarket_id":"P",
           "kalshi_title":"NBA basketball game","polymarket_question":"NBA basketball game",
           "sports_candidate":True,"title_similarity":1}
        b=dict(a,kalshi_ticker="KXPARLAY-FOO",polymarket_id="P2")
        self.assertEqual(shortlist({"candidates":[a,b]})["sports_candidates_returned"],0)
    def test_team_only_sports_title_survives(self):
        a={"kalshi_ticker":"KXNBAGAME-26OCT28OKCDAL-OKC",
           "polymarket_id":"NBA1","kalshi_title":"Oklahoma City Thunder",
           "polymarket_question":"Thunder vs. Mavericks",
           "title_similarity":0.8,"sports_candidate":True}
        result=shortlist({"candidates":[a]})
        self.assertEqual(result["sports_candidates_returned"],1)
        self.assertFalse(result["candidates"][0]["rules_verified"])
    def test_limit(self):
        with self.assertRaises(ValueError): shortlist({},limit=0)
if __name__=="__main__": unittest.main()
