"""Validate saved illustrative outcomes against research-only capital limits."""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

def audit(report):
    problems=[]
    total=Decimal("5000")
    venue=Decimal("2500")
    try:
        total=min(total,Decimal(str(report.get("max_combined_research_budget_usd",5000))))
        venue=min(venue,Decimal(str(report.get("max_per_venue_research_budget_usd",2500))))
        if total<=0 or venue<=0 or not total.is_finite() or not venue.is_finite():
            raise ValueError("Invalid research caps")
    except (ValueError,InvalidOperation,TypeError) as exc:
        problems.append("Invalid capital limits: "+str(exc))
    scenarios=[]
    for item in report.get("rows",[]):
        scenarios.extend([item.get("scenario"),item.get("max_roi_scenario")])
    scenarios.extend(item.get("scenario") for item in report.get("near_misses",[]))
    for i,s in enumerate(scenarios):
        try:
            if not isinstance(s,dict):
                raise ValueError("Missing scenario")
            cost=Decimal(str(s["total_cost_usd"]))
            gain=Decimal(str(s["hypothetical_net_usd"]))
            n=int(s["contracts_each"])
            a=s["venue_allocation"]
            kalshi=Decimal(str(a["kalshi_conservative_funding_reserve_usd"]))
            poly=Decimal(str(a["polymarket_conservative_funding_reserve_usd"]))
            if not all(x.is_finite() for x in (cost,gain,kalshi,poly)):
                raise ValueError("Non-finite value")
            if n<1 or cost<=0 or cost>total or kalshi<0 or poly<0 or kalshi>venue or poly>venue:
                raise ValueError("Capital cap or quantity violation")
            if gain != Decimal(n)-cost:
                raise ValueError("Net profit accounting mismatch")
        except (ValueError,TypeError,KeyError,InvalidOperation) as exc:
            problems.append("Scenario "+str(i)+": "+str(exc))
    return {"research_only":True,"trade_allowed":False,"verified_opportunities":0,
            "scenarios_checked":len(scenarios),"capital_audit_passed":not problems and bool(scenarios),
            "evidence_status":"VALIDATED_SAMPLE" if scenarios and not problems else ("NO_SCENARIOS" if not scenarios and not problems else "AUDIT_FAILED"),
            "issues":problems[:30],
            "warning":"Passing checks only validates arithmetic and configured research caps, not real fills, fee rates or settlement rules."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="depth_fee_illustrative.json")
    p.add_argument("--output",default="capital_audit.json")
    args=p.parse_args()
    result=audit(json.loads(Path(args.input).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
    if result["evidence_status"]=="AUDIT_FAILED":
        raise SystemExit(1)

if __name__=="__main__":
    main()
