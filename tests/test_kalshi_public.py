import io
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from kalshi_public import fetch_markets, snapshot

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
