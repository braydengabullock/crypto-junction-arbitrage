"""Conservative three-snapshot quote-quality research checks; no trading."""
import argparse
import json
from pathlib import Path

def assess(oldest, previous, current, min_pairs=3):
    if min_pairs < 1:
        raise ValueError("min_pairs must be positive")
    snapshots=[oldest,previous,current]
    leagues=sorted(set().union(*(set(s.get("by_league",{})) for s in snapshots)))
    rows={}
    for league in leagues:
        rates=[]
        counts=[]
        for s in snapshots:
            v=s.get("by_league",{}).get(league,{})
            n=int(v.get("pairs",0))
            passed=int(v.get("quality_screen_passed_pairs",0))
            if n < 0 or passed < 0 or passed > n:
                raise ValueError("Invalid sample counts")
            counts.append(n)
            rates.append(round(passed*100/n,1) if n else None)
        eligible=all(n>=min_pairs for n in counts)
        improving=eligible and rates[0]<rates[1]<rates[2]
        rows[league]={"pairs_by_run":counts,"pass_rates_pct_by_run":rates,
                      "minimum_samples_met":eligible,
                      "three_run_improvement_observed":improving,
                      "status":"DESCRIPTIVE_THREE_RUN_IMPROVEMENT" if improving else
                               ("INSUFFICIENT_SAMPLES" if not eligible else "NO_CONSISTENT_IMPROVEMENT")}
    return {"research_only":True,"trade_allowed":False,"verified_opportunities":0,
            "minimum_pairs_per_run":min_pairs,"by_league":rows,
            "warning":"Three observed samples cannot establish predictability, executable liquidity, verified settlement equivalence or actual profit."}

def main():
    p=argparse.ArgumentParser()
    for key in ("oldest","previous","current"):
        p.add_argument("--"+key,required=True)
    p.add_argument("--min-pairs",type=int,default=3)
    p.add_argument("--output",default="league_three_run_quality.json")
    a=p.parse_args()
    out=assess(*(json.loads(Path(getattr(a,key)).read_text()) for key in
                 ("oldest","previous","current")),min_pairs=a.min_pairs)
    Path(a.output).write_text(json.dumps(out,indent=2))
    print(json.dumps({"research_only":True,"by_league":out["by_league"]}))

if __name__=="__main__":
    main()
