"""Audit actual timestamp spacing during the first 24-hour capture window.

No missing observations are invented and no market opportunities are asserted.
"""
import argparse
import json
from datetime import timedelta
from pathlib import Path
from historical_snapshot_replay import timestamp

def evaluate(archive, *, expected_minutes=15, window_hours=24):
    captures=archive.get("captures",[])
    points=sorted({timestamp(c["captured_at"]) for c in captures})
    end=points[-1] if points else None
    start=end-timedelta(hours=window_hours) if end else None
    recent=[t for t in points if t>=start] if start else []
    gaps=[round((b-a).total_seconds()/60,2) for a,b in zip(recent,recent[1:])]
    # This measures only the period covered by evidence, not the missing
    # calendar time before first available capture.
    span=(recent[-1]-recent[0]).total_seconds()/60 if len(recent)>1 else 0
    expected_on_observed_span=int(span//expected_minutes)+1 if recent else 0
    missing_within_span=max(0,expected_on_observed_span-len(recent))
    rows=sum(len(c.get("rows",[])) for c in captures if timestamp(c["captured_at"]) in set(recent))
    return {
        "research_only":True,"trade_allowed":False,
        "window_hours":window_hours,"expected_interval_minutes":expected_minutes,
        "capture_count_in_window":len(recent),
        "first_observation_in_window":recent[0].isoformat() if recent else None,
        "last_observation_in_window":recent[-1].isoformat() if recent else None,
        "observed_span_minutes":round(span,2),
        "expected_captures_within_observed_span":expected_on_observed_span,
        "estimated_missing_captures_within_observed_span":missing_within_span,
        "largest_observed_gap_minutes":max(gaps) if gaps else None,
        "gaps_exceeding_1_5x_target":sum(g>expected_minutes*1.5 for g in gaps),
        "market_rows_observed_in_window":rows,
        "complete_24_hour_monitoring_verified":bool(span>=window_hours*60-expected_minutes and
            missing_within_span==0 and (not gaps or max(gaps)<=expected_minutes*1.5)),
        "warning":"Scheduled GitHub Actions may run late. Counts cover only recovered snapshots, not unseen market movement. Not an execution or profitability claim."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True)
    p.add_argument("--output",default="capture_cadence_report.json")
    a=p.parse_args()
    report=evaluate(json.loads(Path(a.archive).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report))
if __name__=="__main__":
    main()
