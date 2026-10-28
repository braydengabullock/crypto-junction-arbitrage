import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from polymarket_public import fetch_markets, snapshot

class Response:
    def __init__(self,payload):
        self.stream=io.BytesIO(json.dumps(payload).encode())
    def __enter__(self):
        return self.stream
    def __exit__(self,*args):
        return False

class PolymarketPublicTests(unittest.TestCase):
    def test_fetch_and_research_label(self):
        def opener(req,timeout):
            params=parse_qs(urlsplit(req.full_url).query)
            self.assertEqual(params["active"],["true"])
            self.assertEqual(params["closed"],["false"])
            self.assertEqual(timeout,20)
            return Response([{"id":"1","question":"Test","outcomePrices":json.dumps(["0.5","0.5"])}])
        markets,page=fetch_markets(limit=10,opener=opener)
        data=snapshot(markets,page)
        self.assertTrue(data["research_only"])
        self.assertFalse(data["data_quality"]["depth_verified"])
        self.assertTrue(page["complete"])
    def test_reject_bad_response(self):
        with self.assertRaises(ValueError):
            fetch_markets(opener=lambda req,timeout:Response({"markets":[]}))
    def test_reject_invalid_page_size(self):
        with self.assertRaises(ValueError):
            fetch_markets(limit=501)
    def test_page_cap_not_full_coverage(self):
        _,meta=fetch_markets(limit=1,max_pages=1,
          opener=lambda req,timeout:Response([{"id":"1"}]))
        self.assertFalse(meta["complete"])
if __name__=="__main__":
    unittest.main()
