import unittest
from opposing_token_map import make_mapping

class MappingCollisionRegression(unittest.TestCase):
    def test_duplicate_market_identity_fails_closed(self):
        # Same Kalshi ticker offered against two distinct Polymarket markets.
        # Neither should survive a ticker-only mapping dictionary.
        base = {
            "match_method": "sports_identifier_date_teams_research",
            "kalshi_title": "Will New York win?",
            "kalshi_subtitle": "",
            "polymarket_outcomes": '["Knicks","Bulls"]',
            "polymarket_clob_token_ids": '["101","102"]',
            "polymarket_slug": "nba-nyk-chi-2026-10-28",
        }
        event = "KXNBAGAME-26OCT28NYKCHI"
        def pair(mid):
            return [
                dict(base, kalshi_ticker=event+"-NYK", polymarket_id=mid),
                dict(base, kalshi_ticker=event+"-CHI", kalshi_title="Will Chicago win?", polymarket_id=mid),
            ]
        result=make_mapping(pair("market-a")+pair("market-b"))
        self.assertEqual(result["mapped_pairs"],0)
        self.assertEqual(result["ambiguous_tickers_rejected"],2)
        self.assertEqual(result["opposing_token_map"],{})

if __name__=="__main__":
    unittest.main()
