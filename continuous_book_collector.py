"""Optional local high-frequency public-book collector. Not enabled in Actions.

Uses already-reviewed research candidate inputs; does not trade, identify
settlement-equivalent outcomes, refresh markets, or invent historical quotes.
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from candidate_orderbooks import collect
from archive_research_capture import build

def record_once(matches, mapping, output_dir, *, max_pairs=30, fetch_k=None, fetch_p=None, workers=1, unavailable_tokens=None):
    if matches.get("source")!="kalshi_polymarket_title_research" or matches.get("research_only") is not True:
        raise ValueError("Research-only market candidate source required")
    if mapping.get("mapping_method")!="exact_event_id_and_two_unambiguous_outcome_labels" or mapping.get("market_rules_verified") is not False:
        raise ValueError("Explicit unverified outcome mapping required")
    allowed={k.split("|")[0] for k in mapping.get("opposing_token_map",{}) if k.endswith("|YES")}
    kwargs={}
    if fetch_k is not None: kwargs["fetch_k"]=fetch_k
    if fetch_p is not None: kwargs["fetch_p"]=fetch_p
    books=collect(matches.get("candidates",[]),max_pairs=max_pairs,allowed_tickers=allowed,workers=workers,unavailable_tokens=unavailable_tokens,**kwargs)
    archive=build(books,mapping)
    output=Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    # Unique file names prevent losing older observations.
    name=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json"
    target=output/name
    with target.open("x",encoding="utf-8") as f:
        json.dump(archive,f)
    return {"path":str(target),"sampled_pairs":books["sampled_candidates"],
            "stored_book_rows":archive["books_with_observations"],
            "errors":sum(len(r.get("errors",[])) for r in books["rows"]),
            "research_only":True,"trade_allowed":False}

def run(matches,mapping,output_dir,*,interval_seconds=60,iterations=1,
        max_pairs=30,workers=1,clock=time.monotonic,sleeper=time.sleep):
    if not 30<=interval_seconds<=900: raise ValueError("Interval must be 30-900 seconds")
    if not 1<=iterations<=1440: raise ValueError("Bounded iteration count required")
    results=[]
    unavailable_tokens=set()
    for i in range(iterations):
        start=clock()
        result=record_once(matches,mapping,output_dir,max_pairs=max_pairs,workers=workers,unavailable_tokens=unavailable_tokens)
        elapsed=max(0,clock()-start)
        result["cycle_duration_seconds"]=round(elapsed,3)
        result["completed_within_target_interval"]=elapsed<=interval_seconds
        result["interval_target_seconds"]=interval_seconds
        result["cycle_overrun_seconds"]=round(max(0,elapsed-interval_seconds),3)
        results.append(result)
        if i+1<iterations:
            sleeper(max(0,interval_seconds-elapsed))
    return results

def main():
    p=argparse.ArgumentParser(description="Read-only bounded public orderbook captures")
    p.add_argument("--matches",required=True)
    p.add_argument("--mapping",required=True)
    p.add_argument("--output-dir",default="local_market_archives")
    p.add_argument("--interval-seconds",type=int,default=60)
    p.add_argument("--iterations",type=int,default=1)
    p.add_argument("--max-pairs",type=int,default=30)
    p.add_argument("--workers",type=int,default=1,choices=range(1,5))
    a=p.parse_args()
    matches=json.loads(Path(a.matches).read_text(encoding="utf-8"))
    mapping=json.loads(Path(a.mapping).read_text(encoding="utf-8"))
    for result in run(matches,mapping,a.output_dir,interval_seconds=a.interval_seconds,
                      iterations=a.iterations,max_pairs=a.max_pairs,workers=a.workers):
        print(json.dumps(result),flush=True)
if __name__=="__main__": main()
