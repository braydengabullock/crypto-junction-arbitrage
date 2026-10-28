import unittest
from candidate_orderbooks import collect

def candidate(league,number):
    return {"kalshi_ticker":f"KX{league}GAME-26OCT28ABCDEF-AAA{number}",
            "polymarket_id":str(number),"polymarket_clob_token_ids":'["123","456"]'}

class LeagueSamplingTests(unittest.TestCase):
    def test_interleaves_leagues_instead_of_only_first_nba(self):
        candidates=[candidate("NBA",i) for i in range(8)]+[candidate("NHL",i) for i in range(2)]
        result=collect(candidates,max_pairs=4,
                       fetch_k=lambda ticker:{"orderbook_fp":{}},
                       fetch_p=lambda token:{"asks":[]})
        self.assertEqual(result["sampled_candidates"],4)
        self.assertEqual(result["sampled_leagues"],{"NBA":2,"NHL":2})
    def test_distinct_games_before_second_team_side(self):
        first=candidate("NBA",1)
        second=dict(first)
        second["kalshi_ticker"]=first["kalshi_ticker"].rsplit("-",1)[0]+"-BBB"
        other=candidate("NBA",2)
        result=collect([first,second,other],max_pairs=2,
                       fetch_k=lambda ticker:{},fetch_p=lambda token:{})
        self.assertEqual(result["distinct_events_sampled"],2)
        self.assertEqual([r["kalshi_ticker"] for r in result["rows"]],
                         [first["kalshi_ticker"],other["kalshi_ticker"]])
    def test_cap_and_allowed_tickers_remain_enforced(self):
        candidates=[candidate("NBA",1),candidate("NHL",2)]
        result=collect(candidates,max_pairs=2,allowed_tickers={candidates[1]["kalshi_ticker"]},
                       fetch_k=lambda ticker:{},fetch_p=lambda token:{})
        self.assertEqual(result["sampled_candidates"],1)
        self.assertEqual(result["sampled_leagues"],{"NHL":1})
if __name__=="__main__":
    unittest.main()
