import unittest
from sampling_comparison import compare
class SamplingTests(unittest.TestCase):
    def test_positive_sighting_between_interval_checks(self):
        doc={"captures":[
            {"captured_at":"2026-10-28T12:00:00Z","modeled_positive_candidates":0},
            {"captured_at":"2026-10-28T12:01:00Z","modeled_positive_candidates":1},
            {"captured_at":"2026-10-28T12:15:00Z","modeled_positive_candidates":0}]}
        result=compare(doc,interval_minutes=15)
        self.assertEqual(result["observed_captures"],3)
        self.assertEqual(result["downsampled_captures"],2)
        self.assertEqual(result["missed_observed_positive_sightings"],1)
    def test_sparse_data_does_not_invent_missing_opportunities(self):
        result=compare({"captures":[
            {"captured_at":"2026-10-28T12:00:00Z","modeled_positive_candidates":0},
            {"captured_at":"2026-10-28T12:15:00Z","modeled_positive_candidates":0}]})
        self.assertEqual(result["missed_observed_positive_sightings"],0)
if __name__=="__main__":
    unittest.main()
