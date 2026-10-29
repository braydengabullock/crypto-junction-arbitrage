"""Run a research-only backtest from local historical capture files.

Accepts only archives already on disk; never fabricates snapshots, requests
exchange APIs, accesses GitHub Actions, or places orders.
"""
import argparse
import json
from pathlib import Path
from merge_historical_archives import merge
from historical_snapshot_replay import replay
from capture_cadence_report import evaluate as cadence
from sampling_comparison import compare

def run_archive_directory(directory, output_dir):
    root=Path(directory)
    if not root.is_dir(): raise ValueError("Local archive directory does not exist")
    paths=sorted(p for p in root.rglob("*.json") if p.is_file())
    docs=[]
    ignored=0
    for path in paths:
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError):
            ignored+=1
            continue
        if isinstance(data,dict) and data.get("source_type")=="archived_public_orderbook_observations":
            docs.append(data)
        else:
            ignored+=1
    merged=merge(docs)
    result=replay(merged)
    timing=cadence(merged)
    comparison=compare(result)
    output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    for name,data in (("local_backtest_archive.json",merged),
                      ("local_backtest_results.json",result),
                      ("local_backtest_cadence.json",timing),
                      ("local_sampling_comparison.json",comparison)):
        (output/name).write_text(json.dumps(data,indent=2),encoding="utf-8")
    status="PRELIMINARY_REPLAY_COMPLETED" if result["capture_count_accepted"] else "INSUFFICIENT_ARCHIVED_DATA"
    return {"status":status,"files_discovered":len(paths),"archives_accepted_as_input":len(docs),
            "files_ignored":ignored,"captured_snapshots":result["capture_count_accepted"],
            "priced_pair_observations":result["total_priced_pair_observations"],
            "positive_modeled_sightings":result["total_positive_candidate_observations"],
            "distinct_positive_market_pairs":result["distinct_positive_market_pairs_observed"],
            "research_only":True,"historical_execution_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-dir",required=True)
    p.add_argument("--output-dir",default="local_backtest_output")
    a=p.parse_args()
    print(json.dumps(run_archive_directory(a.archive_dir,a.output_dir),indent=2))
if __name__=="__main__": main()
