"""Rank near-break-even observations for research only; never place orders."""
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation

def rank(report, limit=10):
    if not isinstance(report,dict) or not isinstance(report.get("near_misses"),list):
        raise ValueError("Invalid depth screen")
    if not isinstance(limit,int) or not 1<=limit<=100: raise ValueError("Invalid limit")
    rows=[]
    for item in report["near_misses"]:
        scenario=item.get("scenario",{})
        try:
            gain=Decimal(str(scenario["hypothetical_net_usd"]))
            cost=Decimal(str(scenario["total_cost_usd"]))
            quantity=int(scenario["contracts_each"])
            if not gain.is_finite() or not cost.is_finite() or cost<=0 or quantity<1 or cost>100: continue
            gap=max(-gain+Decimal("0.01"),Decimal("0"))
        except (KeyError,ValueError,TypeError,InvalidOperation): continue
        fixed=item.get("fixed_ten_contract_pairs") or {}
        fixed_gain=None
        if fixed.get("contracts_each")==10:
            try:
                fixed_gain=Decimal(str(fixed["hypothetical_net_usd"]))
                if not fixed_gain.is_finite(): fixed_gain=None
            except (KeyError,ValueError,InvalidOperation,TypeError): fixed_gain=None
        rows.append({"kalshi_ticker":item.get("kalshi_ticker"),
                     "polymarket_token_id":item.get("polymarket_token_id"),
                     "kalshi_side":item.get("kalshi_side"),
                     "contracts_each":quantity,"combined_cost_usd":str(cost),
                     "illustrative_net_per_contract_pair_usd":str(gain/quantity),
                     "illustrative_net_usd":str(gain),
                     "cost_reduction_for_one_cent_profit_usd":str(gap),
                     "fixed_ten_contract_pairs":item.get("fixed_ten_contract_pairs"),
                     "quote_quality":item.get("quote_quality",{}),
                     "fixed_ten_gap_to_one_cent_usd":str(max(Decimal("0.01")-fixed_gain,Decimal("0"))) if fixed_gain is not None else None,
                     "monitor_only":True,"rules_verified":False})
    rows.sort(key=lambda x:(Decimal(x["cost_reduction_for_one_cent_profit_usd"]),-Decimal(x["illustrative_net_usd"])))
    return {"research_only":True,"trade_allowed":False,"profit_verified":False,
            "status":"RANKED_NEAR_MISSES_NOT_EXECUTABLE","total_priced":len(rows),
            "watchlist":rows[:limit],"warning":"Illustrative cost assumptions, sequential books, and unverified settlement terms."}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="depth_fee_illustrative.json")
    p.add_argument("--output",default="near_miss_watchlist.json")
    p.add_argument("--limit",type=int,default=10)
    a=p.parse_args()
    result=rank(json.loads(Path(a.input).read_text(encoding="utf-8")),a.limit)
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"total_priced":result["total_priced"],"watchlist_count":len(result["watchlist"])}))
