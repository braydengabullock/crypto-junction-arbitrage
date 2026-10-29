"""Audit actual timestamp spacing during the first 24-hour capture window.

No missing observations are invented and no market opportunities are asserted.
"""
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from historical_snapshot_replay import timestamp

def evaluate(archive, *, expected_minutes=15, window_hours=24, as_of=None):
    captures=archive.get("captures",[])
    points=sorted({timestamp(c["captured_at"]) for c in captures})
    end=as_of if as_of is not None else datetime.now(timezone.utc)
    if end.tzinfo is None: raise ValueError("as_of must include timezone")
    start=end-timedelta(hours=window_hours)
    recent=[t for t in points if start<=t<=end]
    gaps=[round((b-a).total_seconds()/60,2) for a,b in zip(recent,recent[1:])]
    # This measures only the period covered by evidence, not the missing
    # calendar time before first available capture.
    span=(recent[-1]-recent[0]).total_seconds()/60 if len(recent)>1 else 0
    expected_on_observed_span=int(span//expected_minutes)+1 if recent else 0
    missing_within_span=max(0,expected_on_observed_span-len(recent))
    recent_set=set(recent)
    rows=sum(len(c.get("rows",[])) for c in captures if timestamp(c["captured_at"]) in recent_set)
    initial_gap=(recent[0]-start).total_seconds()/60 if recent else window_hours*60
    trailing_gap=(end-recent[-1]).total_seconds()/60 if recent else window_hours*60
    expected_full_window=int(window_hours*60/expected_minutes)
    # Scheduled jobs can start late: this is an approximate count, not proof
    # that each specific wall-clock slot was missed.
    estimated_missing_full_window=max(0,expected_full_window-len(recent))
    return {
        "research_only":True,"trade_allowed":False,
        "window_hours":window_hours,"expected_interval_minutes":expected_minutes,
        "capture_count_in_window":len(recent),
        "expected_captures_in_full_window":expected_full_window,
        "estimated_missing_captures_in_full_window":estimated_missing_full_window,
        "initial_unobserved_gap_minutes":round(initial_gap,2),
        "trailing_unobserved_gap_minutes":round(trailing_gap,2),
        "review_as_of":end.isoformat(),
        "minutes_since_last_observation":round((end-recent[-1]).total_seconds()/60,2) if recent else None,
        "latest_capture_is_stale":(end-recent[-1]).total_seconds()>expected_minutes*90 if recent else True,
        "first_observation_in_window":recent[0].isoformat() if recent else None,
        "last_observation_in_window":recent[-1].isoformat() if recent else None,
        "observed_span_minutes":round(span,2),
        "expected_captures_within_observed_span":expected_on_observed_span,
        "estimated_missing_captures_within_observed_span":missing_within_span,
        "largest_observed_gap_minutes":max(gaps) if gaps else None,
        "gaps_exceeding_1_5x_target":sum(g>expected_minutes*1.5 for g in gaps),
        "market_rows_observed_in_window":rows,
        "complete_24_hour_monitoring_verified":bool(len(recent)>=expected_full_window and
            initial_gap<=expected_minutes*1.5 and trailing_gap<=expected_minutes*1.5 and
            span>=window_hours*60-expected_minutes and
            missing_within_span==0 and (end-recent[-1]).total_seconds()<=expected_minutes*90 and
            (not gaps or max(gaps)<=expected_minutes*1.5)),
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
