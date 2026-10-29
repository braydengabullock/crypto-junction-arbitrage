"""Compare modeled capital efficiency of two selected sizes; research only."""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

def compare(report):
    comparisons=[]
    excluded=0
    for row in report.get("rows",[]):
        high=row.get("scenario") or {}
        efficient=row.get("max_roi_scenario") or {}
        try:
            a=Decimal(str(efficient["total_cost_usd"]))
            b=Decimal(str(high["total_cost_usd"]))
            pa=Decimal(str(efficient["hypothetical_net_usd"]))
            pb=Decimal(str(high["hypothetical_net_usd"]))
            na=int(efficient["contracts_each"])
            nb=int(high["contracts_each"])
            if not all(x.is_finite() for x in (a,b,pa,pb)) or min(a,b)<=0 or min(pa,pb)<=0 or min(na,nb)<=0:
                excluded+=1
                continue
            if b<a or pb<pa:
                excluded+=1
                continue
            more_capital=b-a
            more_profit=pb-pa
            incremental_roi=(more_profit/more_capital*100) if more_capital>0 else None
            incremental_tier=("SAME_SIZE" if incremental_roi is None else
                              "EXCEPTIONAL_2_PLUS" if incremental_roi>=Decimal("2") else
                              "HIGHER_PRIORITY_0_5_PLUS" if incremental_roi>=Decimal("0.5") else
                              "SMALL_POSITIVE" if incremental_roi>0 else "NO_INCREMENTAL_GAIN")
            comparisons.append({
                "kalshi_ticker":row.get("kalshi_ticker"),
                "kalshi_side":row.get("kalshi_side"),
                "polymarket_token_id":row.get("polymarket_token_id"),
                "max_roi_contracts":na,"max_profit_contracts":nb,
                "capital_for_max_roi_usd":str(a),"capital_for_max_profit_usd":str(b),
                "additional_capital_usd":str(more_capital),
                "additional_modeled_profit_usd":str(more_profit),
                "incremental_modeled_roi_pct":str(incremental_roi.quantize(Decimal("0.001"))) if incremental_roi is not None else None,
                "same_sizing":na==nb,
                "incremental_roi_tier":incremental_tier,
                "cost_inputs_verified":False,"candidate_only":True
            })
        except (ValueError,TypeError,KeyError,InvalidOperation,ArithmeticError):
            excluded+=1
            continue
    return {"research_only":True,"trade_allowed":False,"net_profit_verified":False,
            "matched_scenarios_compared":len(comparisons),
            "different_size_count":sum(not x["same_sizing"] for x in comparisons),
            "excluded_incomplete_or_invalid_scenarios":excluded,
            "comparisons":comparisons,
            "warning":"Incremental ROI is purely illustrative. Fee rates, fills, outcome equivalence, and market access remain unverified."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="depth_fee_illustrative.json")
    p.add_argument("--output",default="capital_efficiency.json")
    a=p.parse_args()
    out=compare(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"matched_scenarios_compared":out["matched_scenarios_compared"],
                      "different_size_count":out["different_size_count"],
                      "research_only":True}))
if __name__=="__main__":
    main()
