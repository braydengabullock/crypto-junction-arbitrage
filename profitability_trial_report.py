"""Research-only profitability trial: separate modeled returns from usable evidence."""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

def evaluate(pricing):
    near=pricing.get("near_misses",[])
    bykey={(str(x.get("kalshi_ticker")),str(x.get("kalshi_side")),str(x.get("polymarket_token_id"))):x for x in near}
    reviewed=[]
    excluded=0
    for x in pricing.get("rows",[]):
        try:
            s=x["scenario"]
            profit=Decimal(str(s["hypothetical_net_usd"]))
            cost=Decimal(str(s["total_cost_usd"]))
            size=Decimal(str(s["contracts_each"]))
            if not all(v.is_finite() for v in (profit,cost,size)) or cost<=0 or profit<=0 or size<1 or size!=size.to_integral_value():
                excluded+=1
                continue
            roi=profit/cost*100
            key=(str(x.get("kalshi_ticker")),str(x.get("kalshi_side")),str(x.get("polymarket_token_id")))
            q=bykey.get(key,{}).get("quote_quality",{})
            synchronized=q.get("within_20_seconds") is True
            sufficient_depth=q.get("sufficient_depth_for_ten") is True
            reviewed.append({
                "kalshi_ticker":x.get("kalshi_ticker"),
                "kalshi_side":x.get("kalshi_side"),
                "polymarket_token_id":x.get("polymarket_token_id"),
                "contracts_each":int(size),
                "hypothetical_profit_usd":str(profit),
                "hypothetical_roi_pct":str(roi.quantize(Decimal("0.001"))),
                "quote_observation_within_20_seconds":synchronized,
                "displayed_depth_for_ten":sufficient_depth,
                "requires_independent_rule_fee_fx_and_execution_verification":True,
                "trade_allowed":False,
            })
        except (KeyError,ValueError,TypeError,InvalidOperation,ArithmeticError):
            excluded+=1
    return {"research_only":True,"trade_allowed":False,"verified_profitable_opportunities":0,
            "eligibility_rule":"strictly_positive_modeled_net_after_costs",
            "candidate_pairs_with_positive_modeled_net":len(reviewed),
            "candidate_pairs_eligible_for_research":len(reviewed),
            "positive_candidates_with_short_quote_window":sum(x["quote_observation_within_20_seconds"] for x in reviewed),
            "positive_candidates_with_short_window_and_ten_contract_depth":sum(x["quote_observation_within_20_seconds"] and x["displayed_depth_for_ten"] for x in reviewed),
            "excluded_invalid_positive_rows":excluded,
            "fx_cost_explicitly_modeled":pricing.get("fx_cost_supplied") is True,
            "fee_inputs_verified":False,"rules_verified":False,
            "candidates":reviewed[:50],
            "conclusion":"MODELED_CANDIDATES_NOT_VERIFIED" if reviewed else "NO_POSITIVE_MODELED_CANDIDATES_IN_THIS_SAMPLE",
            "warning":"Not a historical backtest or trading recommendation. Public snapshots are not synchronized executable quotes. Pricing assumptions, FX, outcomes, eligibility and fills remain unverified."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="depth_fee_illustrative.json")
    p.add_argument("--output",default="profitability_trial_report.json")
    a=p.parse_args()
    report=evaluate(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("candidates","warning")}))
if __name__=="__main__":
    main()
