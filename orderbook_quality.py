"""Audit whether sequential public candidate books provide usable research evidence.

No price/profit signals: title matches and raw books are unverified.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from orderbook_research import kalshi_buy_levels, polymarket_buy_levels

def stamp(value):
    parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if parsed.tzinfo is None: raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)

def summarize(payload, *, maximum_lag_seconds=20):
    if payload.get("research_only") is not True or not isinstance(payload.get("rows"),list):
        raise ValueError("Expected research-only candidate book collection")
    report={"research_only":True,"rows_examined":len(payload["rows"]),
            "rows_with_kalshi_and_polymarket_books":0,
            "rows_with_synchronized_observations":0,
            "rows_with_displayed_depth_on_both_venues":0,
            "request_errors":0,"verified_opportunities":0,
            "backtest_ready":False,"details":[]}
    for row in payload["rows"]:
        observations=row.get("observations",[])
        kalshi=[x for x in observations if x.get("venue")=="kalshi"]
        poly=[x for x in observations if x.get("venue")=="polymarket"]
        issue=list(row.get("errors",[]))
        report["request_errors"]+=len(issue)
        both=bool(kalshi and poly)
        synced=False
        has_depth=False
        if both:
            report["rows_with_kalshi_and_polymarket_books"]+=1
            try:
                times=[stamp(kalshi[0]["observed_at"])]+[stamp(x["observed_at"]) for x in poly]
                synced=(max(times)-min(times)).total_seconds() <= maximum_lag_seconds
                # Kalshi YES or NO side may be relevant, but side cannot be
                # selected until equivalence is independently established.
                kbook=kalshi[0]["book"]
                kdepth=bool(kalshi_buy_levels(kbook,"YES") or kalshi_buy_levels(kbook,"NO"))
                pdepth=any(bool(polymarket_buy_levels(x["book"])) for x in poly)
                has_depth=kdepth and pdepth
            except (ValueError,KeyError,TypeError) as exc:
                issue.append("Invalid orderbook structure or timestamp")
        if synced: report["rows_with_synchronized_observations"]+=1
        if has_depth: report["rows_with_displayed_depth_on_both_venues"]+=1
        report["details"].append({"kalshi_ticker":row.get("kalshi_ticker"),
                                  "polymarket_id":row.get("polymarket_id"),
                                  "both_books":both,"synchronized":synced,
                                  "displayed_depth_on_both":has_depth,
                                  "issues":issue,
                                  "rule_equivalence_verified":False})
    report["warning"]="These metrics describe data quality only; neither matched outcomes nor executable fills, fees, capital reuse, eligibility, or profit are verified."
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",default="orderbook_quality.json")
    args=parser.parse_args()
    result=summarize(json.loads(Path(args.input).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("rows_examined","rows_with_synchronized_observations","rows_with_displayed_depth_on_both_venues","verified_opportunities")}))
if __name__=="__main__":
    main()
