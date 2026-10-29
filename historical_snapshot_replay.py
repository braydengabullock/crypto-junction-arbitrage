"""Offline historical snapshot replay. No network calls or order execution.

Input is a JSON object with 'captures': each capture has captured_at,
rows (the candidate_orderbooks rows), and opposing_token_map. Snapshots
must be independently archived historical observations; unit-test fixtures
are never represented as observed market history.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
from depth_fee_screen import screen

def timestamp(raw):
    t=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
    if t.tzinfo is None: raise ValueError("Timezone required")
    return t.astimezone(timezone.utc)

def replay(archive, *, poly_rate="0.05",kalshi_multiplier="1",extra_cost="0.25",
           fx_cost=None,budget="5000",per_venue_budget="2500"):
    if not isinstance(archive.get("captures"),list):
        raise ValueError("Archive needs captures list")
    if archive.get("source_type")!="archived_public_orderbook_observations":
        raise ValueError("Explicit archival provenance required")
    results=[];rejected=[];seen=set()
    for index,capture in enumerate(archive["captures"]):
        try:
            if not isinstance(capture,dict): raise ValueError("Invalid capture")
            t=timestamp(capture["captured_at"])
            key=t.isoformat()
            if key in seen: raise ValueError("Duplicate capture timestamp")
            seen.add(key)
            if not isinstance(capture.get("rows"),list): raise ValueError("Missing books")
            mapping=capture.get("opposing_token_map")
            if not isinstance(mapping,dict): raise ValueError("Missing explicit outcome mapping")
            # Never combine independent captures: price both sides only from this snapshot.
            screened=screen({"rows":capture["rows"]},poly_rate=poly_rate,
                kalshi_multiplier=kalshi_multiplier,extra_cost=extra_cost,
                fx_cost=fx_cost,budget=budget,per_venue_budget=per_venue_budget,
                opposing_tokens=mapping)
            scenarios=[]
            for item in screened["rows"]:
                s=item["scenario"]
                p=Decimal(str(s["hypothetical_net_usd"]))
                if p<=0: continue
                # Quote timings are unknown unless source observations support them.
                quality=next((n.get("quote_quality",{}) for n in screened["near_misses"]
                              if n.get("kalshi_ticker")==item.get("kalshi_ticker")
                              and n.get("kalshi_side")==item.get("kalshi_side")
                              and str(n.get("polymarket_token_id"))==str(item.get("polymarket_token_id"))),{})
                scenarios.append({"kalshi_ticker":item.get("kalshi_ticker"),
                    "side":item.get("kalshi_side"),
                    "polymarket_token_id":item.get("polymarket_token_id"),
                    "contracts_each":s["contracts_each"],
                    "modeled_net_usd":s["hypothetical_net_usd"],
                    "modeled_roi_pct":s["hypothetical_roi_pct"],
                    "quote_within_20_seconds":quality.get("within_20_seconds") is True,
                    "potentially_non_atomic":True})
            results.append({"captured_at":key,"modeled_positive_candidates":len(scenarios),
                            "pairs_with_modeled_prices":screened.get("mapped_pairs_priced",0),
                            "candidates":scenarios[:50]})
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
            rejected.append({"capture_index":index,"reason":str(exc)[:160]})
    results.sort(key=lambda x:x["captured_at"])
    times=[timestamp(x["captured_at"]) for x in results]
    return {"research_only":True,"trade_allowed":False,"historical_execution_verified":False,
        "source_type":"archived_public_orderbook_observations",
        "archive_provenance_note":archive.get("provenance_note"),
        "capture_count_accepted":len(results),"capture_count_rejected":len(rejected),
        "rejected_captures":rejected[:50],
        "first_capture_at":times[0].isoformat() if times else None,
        "last_capture_at":times[-1].isoformat() if times else None,
        "observed_timespan_days":str(Decimal(str((times[-1]-times[0]).total_seconds()))/Decimal("86400")) if len(times)>1 else "0",
        "total_positive_candidate_observations":sum(x["modeled_positive_candidates"] for x in results),
        "total_priced_pair_observations":sum(x["pairs_with_modeled_prices"] for x in results),
        "eligibility_rule":"modeled_net_usd_strictly_greater_than_zero_no_minimum_roi",
        "max_combined_budget_usd":"5000","max_per_venue_budget_usd":"2500",
        "fx_cost_assumed_zero_if_not_explicit":fx_cost is None,
        "captures":results,
        "warning":"Not a realized-performance backtest. Repeated observations are not independent trades. No historical fills, rule equivalence, synchronized quotes or net execution profits verified."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True)
    p.add_argument("--output",default="historical_replay_report.json")
    p.add_argument("--poly-rate",default="0.05")
    p.add_argument("--kalshi-multiplier",default="1")
    p.add_argument("--extra-cost",default="0.25")
    p.add_argument("--fx-cost")
    a=p.parse_args()
    data=json.loads(Path(a.archive).read_text(encoding="utf-8"))
    report=replay(data,poly_rate=a.poly_rate,kalshi_multiplier=a.kalshi_multiplier,
                  extra_cost=a.extra_cost,fx_cost=a.fx_cost)
    Path(a.output).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("captures","rejected_captures","warning")}))
if __name__=="__main__":
    main()
