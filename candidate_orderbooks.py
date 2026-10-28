"""Bounded public order-book sampling of potential title matches.

This deliberately does NOT score profitability: the selected token may not be
the appropriate complementary outcome; fees, settlement rules and eligibility
are not verified. Each request is timestamped and errors are recorded.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from orderbook_research import fetch_kalshi_book, fetch_polymarket_book

def now():
    return datetime.now(timezone.utc).isoformat()

def parse_tokens(value):
    try:
        parsed=json.loads(value) if isinstance(value,str) else value
        if not isinstance(parsed,list): return []
        return [str(t) for t in parsed if str(t).isdigit()]
    except (ValueError,TypeError):
        return []

def collect(candidates, *, max_pairs=5, fetch_k=fetch_kalshi_book,
            fetch_p=fetch_polymarket_book):
    if not isinstance(candidates,list) or not 1<=max_pairs<=20:
        raise ValueError("Invalid candidates or cap")
    rows=[]
    for candidate in candidates[:max_pairs]:
        tokens=parse_tokens(candidate.get("polymarket_clob_token_ids"))
        ticker=candidate.get("kalshi_ticker")
        row={"kalshi_ticker":ticker,"polymarket_id":candidate.get("polymarket_id"),
             "research_only":True,"rule_match_verified":False,
             "executable_opportunity_verified":False,"status":"NOT_VERIFIED",
             "observations":[],"errors":[]}
        if not ticker or not tokens:
            row["errors"].append("Missing Kalshi ticker or Polymarket token IDs")
            rows.append(row);continue
        try:
            started=now()
            book=fetch_k(ticker)
            completed=now()
            row["observations"].append({"venue":"kalshi","request_started_at":started,"observed_at":completed,"book":book})
        except Exception as exc:
            row["errors"].append("Kalshi fetch failed: "+type(exc).__name__)
        for token in tokens[:2]:
            try:
                started=now()
                book=fetch_p(token)
                completed=now()
                row["observations"].append({"venue":"polymarket","token_id":token,
                                             "request_started_at":started,"observed_at":completed,"book":book})
            except Exception as exc:
                row["errors"].append("Polymarket fetch failed: "+type(exc).__name__)
        rows.append(row)
    return {"research_only":True,"verified_opportunities":0,
            "candidate_count":len(candidates),"sampled_candidates":len(rows),
            "captured_at":now(),"rows":rows,
            "warning":"Sequential public books, potentially unmatched outcomes. No claims of trade eligibility, executable fills or net profit."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--matches",required=True)
    p.add_argument("--output",default="candidate_orderbooks.json")
    p.add_argument("--max-pairs",type=int,default=5)
    args=p.parse_args()
    data=json.loads(Path(args.matches).read_text(encoding="utf-8"))
    if data.get("source")!="kalshi_polymarket_title_research" or not data.get("research_only"):
        raise ValueError("Only research candidate lists accepted")
    result=collect(data.get("candidates",[]),max_pairs=args.max_pairs)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"sampled_candidates":result["sampled_candidates"],
                      "verified_opportunities":0,"output":args.output}))
if __name__=="__main__":
    main()
