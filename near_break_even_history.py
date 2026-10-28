"""Carry near-break-even streaks between archived comparison reports (read only)."""
import json
from decimal import Decimal
from pathlib import Path

def update(previous,current):
    old={(str(r.get("kalshi_ticker")),str(r.get("kalshi_side")),str(r.get("polymarket_token_id"))):r for r in previous.get("changes",[])}
    for row in current.get("changes",[]):
        key=(str(row.get("kalshi_ticker")),str(row.get("kalshi_side")),str(row.get("polymarket_token_id")))
        try:
            prior=max(0,min(10000,int(old.get(key,{}).get("near_break_even_streak",0))))
        except (TypeError,ValueError):
            prior=0
        from decimal import Decimal,InvalidOperation
        try:
            v=Decimal(str(row.get("fixed_ten_current_net_usd")))
            close=v.is_finite() and Decimal("-0.25")<=v<0
        except (InvalidOperation,TypeError):
            close=False
        row["near_break_even_streak"]=prior+1 if close and row.get("quote_quality_passed") is True else 0
    current["research_shortlist"]=sorted((r for r in current.get("changes",[]) if r.get("fixed_ten_current_net_usd") is not None and r.get("distance_to_break_even_fixed_ten_usd") is not None),
        key=lambda r:(r.get("quote_quality_passed") is not True,
                      -int(r.get("near_break_even_streak",0)),
                      max(0,-Decimal(str(r["fixed_ten_current_net_usd"])))))[:5]
    current["shortlist_quality_passed"]=sum(r.get("quote_quality_passed") is True for r in current["research_shortlist"])
    current["shortlist_quality_unverified"]=len(current["research_shortlist"])-current["shortlist_quality_passed"]
    current["shortlist_evidence_status"]="QUOTE_TIMING_AND_TEN-CONTRACT_DEPTH_SCREENED; RULES, FEES AND EXECUTION UNVERIFIED"
    current["persistent_near_break_even_pairs"]=sum(r.get("near_break_even_streak",0)>=2 for r in current.get("changes",[]))
    return current

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--previous",required=True)
    p.add_argument("--current",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=update(json.loads(Path(a.previous).read_text()),json.loads(Path(a.current).read_text()))
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({"persistent_near_break_even_pairs":result["persistent_near_break_even_pairs"],"shortlist_quality_passed":result["shortlist_quality_passed"],"shortlist_quality_unverified":result["shortlist_quality_unverified"]}))
