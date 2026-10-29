"""Merge authentic dated research archives without synthesizing historical data."""
import argparse
import json
from pathlib import Path
from historical_snapshot_replay import timestamp

SOURCE="archived_public_orderbook_observations"
def merge(archives):
    captures={}
    rejected=[]
    for i,doc in enumerate(archives):
        if not isinstance(doc,dict) or doc.get("source_type")!=SOURCE or doc.get("research_only") is not True:
            rejected.append({"archive_index":i,"reason":"INVALID_PROVENANCE"})
            continue
        if doc.get("market_rules_verified") is True or doc.get("trade_allowed") is True:
            rejected.append({"archive_index":i,"reason":"UNSUPPORTED_VERIFICATION_CLAIM"})
            continue
        for j,c in enumerate(doc.get("captures",[])):
            try:
                at=timestamp(c["captured_at"]).isoformat()
                if not isinstance(c["rows"],list) or not isinstance(c["opposing_token_map"],dict):
                    raise ValueError("Missing books or outcome map")
                if at in captures:
                    rejected.append({"archive_index":i,"capture_index":j,"reason":"DUPLICATE_CAPTURE_TIME"})
                    continue
                captures[at]={"captured_at":at,"rows":c["rows"],"opposing_token_map":c["opposing_token_map"]}
            except (KeyError,TypeError,ValueError,OverflowError):
                rejected.append({"archive_index":i,"capture_index":j,"reason":"INVALID_CAPTURE"})
    ordered=[captures[t] for t in sorted(captures)]
    days=len({t[:10] for t in captures})
    dates=sorted({t[:10] for t in captures})
    last_30_dates=set()
    if dates:
        from datetime import date, timedelta
        end=date.fromisoformat(dates[-1])
        last_30_dates={(end-timedelta(days=i)).isoformat() for i in range(30)}
    dates_in_30=sorted(set(dates)&last_30_dates)
    return {"source_type":SOURCE,"research_only":True,"trade_allowed":False,
            "market_rules_verified":False,"net_profit_verified":False,
            "provenance_note":"Combined actual archived public orderbook observations; no backfill.",
            "archives_inspected":len(archives),"captures":[*ordered],
            "capture_count":len(ordered),"distinct_utc_dates_observed":days,
            "observed_dates_in_last_30_days_of_dataset":len(dates_in_30),
            "missing_dates_in_last_30_days_of_dataset":30-len(dates_in_30),
            "observed_30_day_date_coverage_pct":str(round(len(dates_in_30)/30*100,2)),
            "historical_30_day_coverage_complete":len(dates_in_30)==30,
            "first_capture_at":ordered[0]["captured_at"] if ordered else None,
            "last_capture_at":ordered[-1]["captured_at"] if ordered else None,
            "rejections":rejected,
            "warning":"Calendar coverage cannot be inferred from first and last capture alone. No fill, rules, fee, FX or venue-execution verification."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archives",nargs="+",required=True)
    p.add_argument("--output",default="merged_historical_archive.json")
    args=p.parse_args()
    out=merge([json.loads(Path(x).read_text(encoding="utf-8")) for x in args.archives])
    Path(args.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k not in ("captures","rejections")}))
if __name__=="__main__":
    main()
