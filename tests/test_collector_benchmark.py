import unittest
from collector_benchmark import benchmark

class CollectorBenchmarkTests(unittest.TestCase):
    def test_offline_benchmark_archives_without_network(self):
        r=benchmark(pairs=3,iterations=2,latency_ms=0)
        self.assertEqual(r["network_calls"],0)
        self.assertEqual(r["archived_snapshots"],2)
        self.assertEqual(r["simulated_requests_per_cycle"],9)
        self.assertEqual(r["simulated_total_requests"],18)
        self.assertEqual(r["cycles_within_target"],2)
        self.assertFalse(r["trade_allowed"])
    def test_rejects_excessive_benchmark_workload(self):
        with self.assertRaises(ValueError):
            benchmark(pairs=31)
        with self.assertRaises(ValueError):
            benchmark(latency_ms=1001)
if __name__=="__main__":
    unittest.main()
