import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from capture_kalshi import capture

class CaptureTests(unittest.TestCase):
    def test_snapshot_retains_timestamp_and_limitations(self):
        fake=[{"ticker":"TEST-1","title":"Mock event","status":"open","yes_ask_dollars":"0.45"}]
        with tempfile.TemporaryDirectory() as folder:
            with patch("capture_kalshi.fetch_markets",return_value=fake) as source:
                path=capture(limit=1,output_dir=folder)
            self.assertTrue(Path(path).is_file())
            data=json.loads(Path(path).read_text())
            self.assertEqual(data["markets"][0]["ticker"],"TEST-1")
            self.assertFalse(data["data_quality"]["depth_verified"])
            self.assertFalse(data["data_quality"]["forecast_ex_match_verified"])
            self.assertIn("observed_at",data)
            source.assert_called_once_with(limit=1,event_ticker=None)

if __name__=="__main__":
    unittest.main()
