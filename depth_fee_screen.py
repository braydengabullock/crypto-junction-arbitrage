"""Read-only displayed-depth screening using explicit hypothetical fee inputs.

Cannot certify real net profit: contract outcome mapping/rules and actual fee rates
still require independent verification. Never places orders.
"""
import json
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from orderbook_research import kalshi_buy_levels,polymarket_buy_levels,depth_cost
from fee_estimates import kalshi_general_taker_fee,polymarket_sports_taker_fee,positive

def roi_tier(profit, cost):
    """Research classification only: any strictly positive net is eligible for review."""
    if cost <= 0 or profit <= 0:
        return "NONPOSITIVE_REJECT"
    pct=profit/cost*100
    if pct >= Decimal("2"):
        return "EXCEPTIONAL_2_PLUS"
    if pct >= Decimal("0.5"):
        return "HIGHER_PRIORITY_0_5_PLUS"
    return "SMALL_POSITIVE"

def screen(data, *, poly_rate=None,kalshi_multiplier=None,extra_cost=None,budget="100",opposing_tokens=None):
    result={"research_only":True,"trade_allowed":False,"fee_inputs_verified":False,
            "market_rules_verified":False,"net_profit_verified":False,
            "status":"FEE_INPUTS_REQUIRED","rows":[],"near_misses":[]}
    if any(v is None for v in (poly_rate,kalshi_multiplier,extra_cost)):
        return result
    cap=positive(budget)
    if cap>100: raise ValueError("Combined $100 budget ceiling")
    fixed=positive(extra_cost); rate=positive(poly_rate); mult=positive(kalshi_multiplier)
    result["status"]="OPPOSING_OUTCOME_MAPPING_REQUIRED" if opposing_tokens is None else "ILLUSTRATIVE_ONLY_UNVERIFIED_RULES_AND_FEES"
    if opposing_tokens is None: return result
    if not isinstance(opposing_tokens,dict): raise ValueError("Explicit opposing outcome mapping must be an object")
    for row in data.get("rows",[]):
        ko=next((o for o in row.get("observations",[]) if o.get("venue")=="kalshi"),None)
        ps=[o for o in row.get("observations",[]) if o.get("venue")=="polymarket"]
        if not ko or not ps: continue
        for side in ("YES","NO"):
            allowed=opposing_tokens.get(str(row.get("kalshi_ticker"))+"|"+side)
            if not allowed: continue
            for po in ps:
                if str(po.get("token_id"))!=str(allowed): continue
                try:
                    kl=kalshi_buy_levels(ko["book"],side)
                    pl=polymarket_buy_levels(po["book"])
                    if not kl or not pl: continue
                    best=None
                    closest=None
                    fixed_ten=None
                    quote_quality={"both_books_present":True,"max_observation_span_seconds":None,"within_20_seconds":False,"sufficient_depth_for_ten":False}
                    try:
                        start=min(datetime.fromisoformat(str(x["request_started_at"]).replace("Z","+00:00")) for x in (ko,po))
                        end=max(datetime.fromisoformat(str(x["observed_at"]).replace("Z","+00:00")) for x in (ko,po))
                        span=(end-start).total_seconds()
                        if span>=0:
                            quote_quality["max_observation_span_seconds"]=span
                            quote_quality["within_20_seconds"]=span<=20
                    except (KeyError,ValueError,TypeError):
                        pass
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
                        allocation={"kalshi_displayed_usd":str(kc["displayed_cost_usd"]),
                                    "polymarket_displayed_usd":str(pc["displayed_cost_usd"]),
                                    "modeled_fees_and_extra_usd":str(kfee+pfee+fixed)}
                        if n==10:
                            quote_quality["sufficient_depth_for_ten"]=True
                            fixed_ten={"contracts_each":10,"total_cost_usd":str(total),
                                       "hypothetical_net_usd":str(profit),
                                       "net_roi_tier":roi_tier(profit,total),
                                       "displayed_kalshi_cost_usd":str(kc["displayed_cost_usd"]),
                                       "displayed_polymarket_cost_usd":str(pc["displayed_cost_usd"]),
                                       "raw_displayed_spread_usd":str(Decimal(n)-Decimal(kc["displayed_cost_usd"])-Decimal(pc["displayed_cost_usd"])),
                                       "modeled_kalshi_fee_usd":str(kfee),
                                       "modeled_polymarket_fee_usd":str(pfee),
                                       "assumed_extra_cost_usd":str(fixed),
                                       "modeled_total_friction_usd":str(kfee+pfee+fixed)}
                        if closest is None or profit>Decimal(closest["hypothetical_net_usd"]):
                            closest={"contracts_each":n,"total_cost_usd":str(total),
                                     "hypothetical_net_usd":str(profit),
                                     "net_roi_tier":roi_tier(profit,total),"venue_allocation":allocation,
                                     "minimum_total_cost_reduction_to_positive_usd":str((-profit if profit<0 else Decimal("0"))+Decimal("0.01")) if profit<=0 else "0",
                                     "minimum_reduction_per_contract_pair_usd":str((((-profit if profit<0 else Decimal("0"))+Decimal("0.01"))/n).quantize(Decimal("0.00001"))) if profit<=0 else "0",
                                     "hypothetical_roi_pct":str((profit/total*100).quantize(Decimal("0.001")))}
                        if profit>0 and (best is None or profit>Decimal(best["hypothetical_net_usd"])):
                            best={"contracts_each":n,"total_cost_usd":str(total),
                                  "hypothetical_net_usd":str(profit),
                                  "net_roi_tier":roi_tier(profit,total),"venue_allocation":allocation,
                                  "hypothetical_roi_pct":str((profit/total*100).quantize(Decimal("0.001")))}
                    if closest:
                        result["near_misses"].append({"kalshi_ticker":row.get("kalshi_ticker"),
                            "kalshi_side":side,"polymarket_token_id":po.get("token_id"),
                            "scenario":closest,"fixed_ten_contract_pairs":fixed_ten,
                            "quote_quality":quote_quality,
                            "candidate_only":True,"settlement_rules_verified":False})
                    if best:
                        result["rows"].append({"kalshi_ticker":row.get("kalshi_ticker"),
                             "kalshi_side":side,"polymarket_token_id":po.get("token_id"),
                             "scenario":best,"opposite_outcome_verified":False,
                             "opposite_outcome_mapping_supplied":True,
                             "candidate_only":True})
                except (ValueError,KeyError,TypeError,ArithmeticError):
                    continue
    result["rows"].sort(key=lambda r:Decimal(r["scenario"]["hypothetical_net_usd"]),reverse=True)
    result["candidate_scenarios"]=len(result["rows"])
    result["near_misses"].sort(key=lambda x:Decimal(x["scenario"]["hypothetical_net_usd"]),reverse=True)
    result["mapped_pairs_priced"]=len(result["near_misses"])
    return result

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--books",default="candidate_orderbooks.json")
    a.add_argument("--output",default="depth_fee_screen.json")
    a.add_argument("--poly-rate")
    a.add_argument("--kalshi-multiplier")
    a.add_argument("--extra-cost")
    a.add_argument("--opposing-token-map",help="Reviewed ticker|side to opposite Polymarket token mapping JSON")
    z=a.parse_args()
    data=json.loads(Path(z.books).read_text(encoding="utf-8"))
    mapping=json.loads(Path(z.opposing_token_map).read_text(encoding="utf-8")) if z.opposing_token_map else None
    if mapping is not None:
        if mapping.get("mapping_method")!="exact_event_id_and_two_unambiguous_outcome_labels" or mapping.get("market_rules_verified") is not False:
            raise ValueError("Unsupported or incorrectly certified outcome mapping")
        mapping=mapping["opposing_token_map"]
    out=screen(data,poly_rate=z.poly_rate,kalshi_multiplier=z.kalshi_multiplier,extra_cost=z.extra_cost,opposing_tokens=mapping)
    Path(z.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"status":out["status"],"candidate_scenarios":len(out["rows"]),
                      "net_profit_verified":False,"mapped_pairs_priced":out.get("mapped_pairs_priced",0),
                      "best_illustrative_net_usd":out["near_misses"][0]["scenario"]["hypothetical_net_usd"] if out["near_misses"] else None}))
