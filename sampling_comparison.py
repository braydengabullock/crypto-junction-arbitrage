"""Compare cadence visibility using only genuinely observed replay snapshots.

This is retrospective downsampling, not interpolation: missing intra-interval
opportunities cannot be inferred from sparse recordings.
"""
import argparse
import json
from pathlib import Path
from historical_snapshot_replay import timestamp

def compare(report, *, interval_minutes=15):
    captures=report.get("captures",[])
    if not isinstance(captures,list) or interval_minutes<=0:
        raise ValueError("Expected replay captures and positive interval")
    ordered=sorted(captures,key=lambda c:timestamp(c["captured_at"]))
    if not ordered:
        return {"research_only":True,"observed_captures":0,"downsampled_captures":0,
                "all_observed_positive_sightings":0,"downsampled_positive_sightings":0,
                "missed_observed_positive_sightings":0,"warning":"No observations available."}
    origin=timestamp(ordered[0]["captured_at"])
    buckets={}
    for item in ordered:
        t=timestamp(item["captured_at"])
        slot=int((t-origin).total_seconds()//(interval_minutes*60))
        buckets.setdefault(slot,item)  # first recorded observation in each interval
    reduced=list(buckets.values())
    positive=lambda rows:sum(int(x.get("modeled_positive_candidates",0)) for x in rows)
    all_pos=positive(ordered)
    sampled_pos=positive(reduced)
    return {"research_only":True,"trade_allowed":False,
            "interval_minutes":interval_minutes,
            "observed_captures":len(ordered),"downsampled_captures":len(reduced),
            "all_observed_positive_sightings":all_pos,
            "downsampled_positive_sightings":sampled_pos,
            "missed_observed_positive_sightings":all_pos-sampled_pos,
            "warning":"Only compares actual collected snapshots. Cannot estimate missed opportunities between observations; sightings are not executable trades."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--replay",required=True)
    p.add_argument("--output",default="sampling_comparison.json")
    a=p.parse_args()
    result=compare(json.loads(Path(a.replay).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
if __name__=="__main__":
    main()
