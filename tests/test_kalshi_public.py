import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from kalshi_public import fetch_markets, fetch_market_pages, snapshot

class FakeResponse:
    def __init__(self, payload):
        self.payload = io.BytesIO(json.dumps(payload).encode())
    def __enter__(self):
        return self.payload
    def __exit__(self, *args):
        return False

class KalshiPublicTests(unittest.TestCase):
    def test_public_market_request(self):
        def opener(req, timeout):
            parsed = urlsplit(req.full_url)
            self.assertEqual(parsed.path, "/trade-api/v2/markets")
            self.assertEqual(parse_qs(parsed.query)["status"], ["open"])
            self.assertEqual(parse_qs(parsed.query)["event_ticker"], ["TEST"])
            self.assertEqual(timeout, 20)
            return FakeResponse({"markets": [{"ticker": "ABC", "status": "open"}]})
        self.assertEqual(fetch_markets(5, "TEST", opener=opener)[0]["ticker"], "ABC")
    def test_cursor_pages_and_completeness(self):
        calls = []
        def opener(req, timeout):
            q = parse_qs(urlsplit(req.full_url).query)
            calls.append(q)
            if len(calls) == 1:
                return FakeResponse({"markets":[{"ticker":"A"}],"cursor":"next"})
            return FakeResponse({"markets":[{"ticker":"B"}],"cursor":""})
        rows, meta = fetch_market_pages(page_size=1,max_pages=3,opener=opener)
        self.assertEqual([m["ticker"] for m in rows],["A","B"])
        self.assertEqual(calls[1]["cursor"],["next"])
        self.assertTrue(meta["complete"])
        self.assertEqual(meta["pages_fetched"],2)
    def test_page_cap_is_explicitly_partial(self):
        rows, meta = fetch_market_pages(page_size=1,max_pages=1,opener=lambda req,timeout:
                     FakeResponse({"markets":[{"ticker":"A"}],"cursor":"more"}))
        self.assertFalse(meta["complete"])
        self.assertEqual(len(rows),1)
    def test_repeated_cursor_is_rejected(self):
        with self.assertRaises(ValueError):
            fetch_market_pages(page_size=1,max_pages=3,opener=lambda req,timeout:
                FakeResponse({"markets":[{"ticker":"A"}],"cursor":"same"}))
    def test_no_inferred_matching_or_execution(self):
        snap = snapshot([{"ticker": "ABC", "yes_ask_dollars": "0.42"}])
        self.assertTrue(snap["research_only"])
        self.assertEqual(snap["markets"][0]["ticker"], "ABC")
        self.assertNotIn("profit", snap["markets"][0])
    def test_reject_invalid_response(self):
        with self.assertRaises(ValueError):
            fetch_markets(opener=lambda req, timeout: FakeResponse({"wrong": []}))
    def test_reject_large_requests(self):
        with self.assertRaises(ValueError):
            fetch_markets(1000)

if __name__ == "__main__":
    unittest.main()
