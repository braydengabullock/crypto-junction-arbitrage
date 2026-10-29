"""Offline timing benchmark for the high-frequency collector.

No network calls: simulated read-only fetches measure per-cycle overhead and
confirm that overruns are visible. This is not an API throughput claim.
"""
import argparse
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from continuous_book_collector import run

def benchmark(*, pairs=30, iterations=3, interval_seconds=60, latency_ms=0):
    if not 1<=pairs<=30 or not 1<=iterations<=20 or not 0<=latency_ms<=1000:
        raise ValueError("Invalid bounded benchmark settings")
    candidates=[{"kalshi_ticker":f"K{i}","polymarket_clob_token_ids":json.dumps([str(i+100000)])}
                for i in range(pairs)]
    matches={"source":"kalshi_polymarket_title_research","research_only":True,"candidates":candidates}
    mapping={"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
             "market_rules_verified":False,"opposing_token_map":{f"K{i}|YES":str(i+100000) for i in range(pairs)}}
    def fetch_k(_):
        time.sleep(latency_ms/1000)
        return {"orderbook_fp":{"yes_dollars":[],"no_dollars":[]}}
    def fetch_p(_):
        time.sleep(latency_ms/1000)
        return {"asks":[]}
    with tempfile.TemporaryDirectory() as d:
        # Avoid idle waiting between simulated cycles, while still measuring actual collection.
        with patch("continuous_book_collector.collect") as collector:
            from candidate_orderbooks import collect
            collector.side_effect=lambda candidates,**kw: collect(candidates,fetch_k=fetch_k,fetch_p=fetch_p,
                max_pairs=kw["max_pairs"],allowed_tickers=kw["allowed_tickers"])
            rows=run(matches,mapping,d,interval_seconds=interval_seconds,iterations=iterations,sleeper=lambda _:None)
        files=len(list(Path(d).glob("*.json")))
    durations=[r["cycle_duration_seconds"] for r in rows]
    return {"benchmark_type":"OFFLINE_SIMULATED_LATENCY","network_calls":0,"research_only":True,
            "trade_allowed":False,"pairs":pairs,"iterations":iterations,
            "simulated_latency_per_request_ms":latency_ms,
            "interval_target_seconds":interval_seconds,
            "cycles_within_target":sum(r["completed_within_target_interval"] for r in rows),
            "maximum_cycle_duration_seconds":max(durations),
            "average_cycle_duration_seconds":round(sum(durations)/len(durations),3),
            "archived_snapshots":files,
            "warning":"Synthetic API latency only; real exchange throughput, throttling and quote freshness untested."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pairs",type=int,default=30)
    p.add_argument("--iterations",type=int,default=3)
    p.add_argument("--interval-seconds",type=int,default=60)
    p.add_argument("--latency-ms",type=int,default=0)
    p.add_argument("--output",default="collector_benchmark.json")
    a=p.parse_args()
    result=benchmark(pairs=a.pairs,iterations=a.iterations,
        interval_seconds=a.interval_seconds,latency_ms=a.latency_ms)
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
if __name__=="__main__": main()
