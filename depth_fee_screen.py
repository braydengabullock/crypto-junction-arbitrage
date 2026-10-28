"""Read-only displayed-depth screening using explicit hypothetical fee inputs.

Cannot certify real net profit: contract outcome mapping/rules and actual fee rates
still require independent verification. Never places orders.
"""
import json
from pathlib import Path
from decimal import Decimal
from orderbook_research import kalshi_buy_levels,polymarket_buy_levels,depth_cost
from fee_estimates import kalshi_general_taker_fee,polymarket_sports_taker_fee,positive

def screen(data, *, poly_rate=None,kalshi_multiplier=None,extra_cost=None,budget="100"):
    result={"research_only":True,"trade_allowed":False,"fee_inputs_verified":False,
            "market_rules_verified":False,"net_profit_verified":False,
            "status":"FEE_INPUTS_REQUIRED","rows":[]}
    if any(v is None for v in (poly_rate,kalshi_multiplier,extra_cost)):
        return result
    cap=positive(budget)
    if cap>100: raise ValueError("Combined $100 budget ceiling")
    fixed=positive(extra_cost); rate=positive(poly_rate); mult=positive(kalshi_multiplier)
    result["status"]="ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES"
    for row in data.get("rows",[]):
        ko=next((o for o in row.get("observations",[]) if o.get("venue")=="kalshi"),None)
        ps=[o for o in row.get("observations",[]) if o.get("venue")=="polymarket"]
        if not ko or not ps: continue
        for side in ("YES","NO"):
            for po in ps:
                try:
                    kl=kalshi_buy_levels(ko["book"],side)
                    pl=polymarket_buy_levels(po["book"])
                    if not kl or not pl: continue
                    best=None
                    for n in range(1,101):
                        kc=depth_cost(kl,n);pc=depth_cost(pl,n)
                        if not (kc["depth_sufficient"] and pc["depth_sufficient"]): break
                        # Fee curve evaluated on the cost-weighted displayed average
                        kp=Decimal(kc["displayed_cost_usd"])/n
                        pp=Decimal(pc["displayed_cost_usd"])/n
                        kfee=kalshi_general_taker_fee(n,kp,multiplier=mult)
                        pfee=polymarket_sports_taker_fee(n,pp,rate=rate)
                        total=Decimal(kc["displayed_cost_usd"])+Decimal(pc["displayed_cost_usd"])+kfee+pfee+fixed
                        if total>cap: break
                        profit=Decimal(n)-total
                        if profit>0 and (best is None or profit>Decimal(best["hypothetical_net_usd"])):
                            best={"contracts_each":n,"total_cost_usd":str(total),
                                  "hypothetical_net_usd":str(profit),
                                  "hypothetical_roi_pct":str((profit/total*100).quantize(Decimal("0.001")))}
                    if best:
                        result["rows"].append({"kalshi_ticker":row.get("kalshi_ticker"),
                             "kalshi_side":side,"polymarket_token_id":po.get("token_id"),
                             "scenario":best,"opposite_outcome_verified":False,
                             "candidate_only":True})
                except (ValueError,KeyError,TypeError,ArithmeticError):
                    continue
    result["rows"].sort(key=lambda r:Decimal(r["scenario"]["hypothetical_net_usd"]),reverse=True)
    result["candidate_scenarios"]=len(result["rows"])
    return result

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--books",default="candidate_orderbooks.json")
    a.add_argument("--output",default="depth_fee_screen.json")
    a.add_argument("--poly-rate")
    a.add_argument("--kalshi-multiplier")
    a.add_argument("--extra-cost")
    z=a.parse_args()
    data=json.loads(Path(z.books).read_text(encoding="utf-8"))
    out=screen(data,poly_rate=z.poly_rate,kalshi_multiplier=z.kalshi_multiplier,extra_cost=z.extra_cost)
    Path(z.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"status":out["status"],"candidate_scenarios":len(out["rows"]),
                      "net_profit_verified":False}))
