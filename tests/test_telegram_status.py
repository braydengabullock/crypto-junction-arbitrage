import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from telegram_status import send_status, status_message

class Response:
    def __enter__(self):
        return io.BytesIO(b'{"ok":true}')
    def __exit__(self,*args):
        return False

class TelegramStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"snapshot.json"
        self.path.write_text(json.dumps({
            "source":"kalshi_public","research_only":True,
            "observed_at":"2026-10-27T18:00:00+00:00",
            "data_quality":{"market_count":5},
            "markets":[{"ticker":"DEMO"}]
        }))
    def tearDown(self):
        self.temp.cleanup()
    def test_status_accurately_labels_data(self):
        msg=status_message(self.path)
        self.assertIn("ForecastEx feed: NOT CONNECTED",msg)
        self.assertIn("Verified opportunities: NONE",msg)
    def test_no_credentials_no_telegram(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertFalse(send_status(self.path))
    def test_can_send_to_fake_transport(self):
        called=[]
        def fake(req,timeout):
            called.append(req)
            return Response()
        with patch.dict("os.environ",{
            "CJ_ARB_TELEGRAM_BOT_TOKEN":"example",
            "CJ_ARB_TELEGRAM_CHAT_ID":"123"}):
            self.assertTrue(send_status(self.path,sender=fake))
        self.assertEqual(len(called),1)
        self.assertIn(b"Arbitrage+Research+Status",called[0].data)
    def test_reject_nonresearch_snapshot(self):
        self.path.write_text('{"source":"untrusted","research_only":false}')
        with self.assertRaises(ValueError):
            status_message(self.path)

if __name__=="__main__":
    unittest.main()
