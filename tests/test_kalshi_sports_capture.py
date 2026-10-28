import unittest
from kalshi_sports_capture import capture_sports
class SportsCaptureTests(unittest.TestCase):
 def test_series_filters_and_output(self):
  seen=[]
  def fake(**kwargs):
   seen.append(kwargs["series_ticker"])
   return ([{"ticker":kwargs["series_ticker"]+"-ABC","title":"Example"}],
           {"complete":True,"pages_fetched":1})
  result=capture_sports(fetch=fake,series=("KXNBAGAME","KXNHLGAME"))
  self.assertEqual(len(result["markets"]),2)
  self.assertEqual(seen,["KXNBAGAME","KXNHLGAME"])
  self.assertTrue(result["data_quality"]["all_series_complete"])
 def test_partial_series_is_not_complete(self):
  def fake(**kw): raise ValueError("Bad response")
  r=capture_sports(fetch=fake,series=("KXNBAGAME",))
  self.assertFalse(r["data_quality"]["all_series_complete"])
if __name__=="__main__":unittest.main()
