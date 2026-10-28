"""Bounded public order-book sampling of potential title matches.

This deliberately does NOT score profitability: the selected token may not be
the appropriate complementary outcome; fees, settlement rules and eligibility
are not verified. Each request is timestamped and errors are recorded.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
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
            fetch_p=fetch_polymarket_book, allowed_tickers=None):
    if not isinstance(candidates,list) or not 1<=max_pairs<=20:
        raise ValueError("Invalid candidates or cap")
    rows=[]
    selected=[c for c in candidates if allowed_tickers is None or c.get("kalshi_ticker") in allowed_tickers]
    # Interleave eligible leagues instead of consuming the first N (usually NBA).
    buckets={}
    for candidate in selected:
        ticker=str(candidate.get("kalshi_ticker") or "")
        league=ticker.split("GAME-",1)[0].removeprefix("KX") if "GAME-" in ticker else "OTHER"
        buckets.setdefault(league,[]).append(candidate)
    ordered=[]
    while any(buckets.values()):
        for league in sorted(buckets):
            if buckets[league]:
                ordered.append(buckets[league].pop(0))
    sampled=ordered[:max_pairs]
    for candidate in sampled:
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
            except HTTPError as exc:
                category = {400:"INVALID_TOKEN",404:"NO_ORDERBOOK",429:"RATE_LIMITED"}.get(exc.code,"HTTP_ERROR")
                row["errors"].append("Polymarket "+category+" HTTP "+str(exc.code))
            except Exception as exc:
                row["errors"].append("Polymarket fetch failed: "+type(exc).__name__)
        rows.append(row)
    league_counts=Counter(str(r.get("kalshi_ticker") or "").split("GAME-",1)[0].removeprefix("KX") for r in rows)
    return {"research_only":True,"verified_opportunities":0,
            "candidate_count":len(candidates),"eligible_candidate_count":len(selected),"sampled_candidates":len(rows),
            "captured_at":now(),"sampled_leagues":dict(sorted(league_counts.items())),"rows":rows,
            "warning":"Sequential public books, potentially unmatched outcomes. No claims of trade eligibility, executable fills or net profit."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--matches",required=True)
    p.add_argument("--output",default="candidate_orderbooks.json")
    p.add_argument("--max-pairs",type=int,default=5)
    p.add_argument("--opposing-token-map",help="Restrict samples to conservatively mapped game-winner tickers")
    args=p.parse_args()
    data=json.loads(Path(args.matches).read_text(encoding="utf-8"))
    if data.get("source")!="kalshi_polymarket_title_research" or not data.get("research_only"):
        raise ValueError("Only research candidate lists accepted")
    allowed=None
    if args.opposing_token_map:
        mapping=json.loads(Path(args.opposing_token_map).read_text(encoding="utf-8"))
        if mapping.get("mapping_method")!="exact_event_id_and_two_unambiguous_outcome_labels":
            raise ValueError("Unsupported outcome mapping")
        allowed={key.split("|")[0] for key in mapping.get("opposing_token_map",{}) if key.endswith("|YES")}
    result=collect(data.get("candidates",[]),max_pairs=args.max_pairs,allowed_tickers=allowed)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"sampled_candidates":result["sampled_candidates"],
                      "verified_opportunities":0,"sampled_leagues":result["sampled_leagues"],"output":args.output}))
if __name__=="__main__":
    main()
