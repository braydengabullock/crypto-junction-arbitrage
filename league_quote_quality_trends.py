"""Compare quality-screened quote counts between research snapshots (no trading)."""
import argparse
import json
from pathlib import Path

def compare(previous, current):
    prev=previous.get("by_league",{})
    curr=current.get("by_league",{})
    rows={}
    for league in sorted(set(prev)|set(curr)):
        a=prev.get(league,{})
        b=curr.get(league,{})
        old_n=int(a.get("pairs",0))
        new_n=int(b.get("pairs",0))
        old_pass=int(a.get("quality_screen_passed_pairs",0))
        new_pass=int(b.get("quality_screen_passed_pairs",0))
        if any(v<0 for v in (old_n,new_n,old_pass,new_pass)) or old_pass>old_n or new_pass>new_n:
            raise ValueError("Invalid quote quality counts")
        old_rate=round(old_pass/old_n*100,1) if old_n else None
        new_rate=round(new_pass/new_n*100,1) if new_n else None
        rows[league]={
            "previous_pairs":old_n,"current_pairs":new_n,
            "previous_passed":old_pass,"current_passed":new_pass,
            "previous_pass_rate_pct":old_rate,"current_pass_rate_pct":new_rate,
            "change_percentage_points":round(new_rate-old_rate,1) if old_rate is not None and new_rate is not None else None,
            "status":"COMPARABLE_RESEARCH" if old_n and new_n else "INSUFFICIENT_SAMPLES",
            "sample_change_pct":round((new_n-old_n)/old_n*100,1) if old_n else None,
            "interpretation":"DESCRIPTIVE_ONLY_NOT_STABLE_TREND"
        }
    return {"research_only":True,"trade_allowed":False,"verified_opportunities":0,
            "by_league":rows,
            "warning":"Only two sequential research snapshots. Different markets, timing, sample sizes and non-atomic public books prevent performance or profitability conclusions."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--previous",required=True)
    p.add_argument("--current",required=True)
    p.add_argument("--output",default="league_quote_quality_trends.json")
    a=p.parse_args()
    out=compare(json.loads(Path(a.previous).read_text()),json.loads(Path(a.current).read_text()))
    Path(a.output).write_text(json.dumps(out,indent=2))
    print(json.dumps({"research_only":True,"by_league":out["by_league"],"verified_opportunities":0}))

if __name__=="__main__":
    main()
