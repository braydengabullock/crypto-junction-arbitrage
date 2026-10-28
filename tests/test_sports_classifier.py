import unittest
from market_comparison import is_sports_candidate, tokenize
class SportsClassificationTests(unittest.TestCase):
 def test_team_only_game_by_series_and_slug(self):
  self.assertTrue(is_sports_candidate(
    {"ticker":"KXNBAGAME-26OCT28OKCDAL-OKC"},
    {"slug":"nba-okc-dal-2026-10-28"},
    tokenize("Thunder Mavericks")))
 def test_unrelated_titles_not_sports(self):
  self.assertFalse(is_sports_candidate(
    {"ticker":"KXECONOMY-FOO"},{"slug":"economy-foo"},
    tokenize("rates rise")))
 def test_sports_ticker_alone_insufficient(self):
  self.assertFalse(is_sports_candidate(
    {"ticker":"KXNBAGAME-ABC"},{"slug":"politics-election"},
    tokenize("Alpha Beta")))
if __name__=="__main__": unittest.main()
