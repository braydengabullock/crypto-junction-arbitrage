"""Create the two opposite-side research combinations without inventing quotes.

Prices are NOT calculated from Gamma outcomePrices, since those are indicative.
"""
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
from one_event_outcome_pairs import outcomes

def combinations(report):
    pairs=report.get("exact_outcome_candidates",[])
    if len(pairs)!=2 or len({p.get("team") for p in pairs})!=2:
        return {"research_only":True,"status":"NO_EXACT_TWO_OUTCOME_PAIR",
                "combinations":[],"net_roi_verified":False}
    indicative={}
    for m in report.get("polymarket_contracts",[]):
        labels=outcomes(m.get("outcomes"))
        tokens=outcomes(m.get("clobTokenIds"))
        prices=outcomes(m.get("indicative_outcome_prices"))
        if len(labels)==len(tokens)==len(prices)==2:
            for token,price in zip(tokens,prices):
                try:
                    value=Decimal(str(price))
                    if value.is_finite() and 0<=value<=1:
                        indicative[str(token)]=value
                except (InvalidOperation,ValueError): pass
    result=[]
    for left,right in ((pairs[0],pairs[1]),(pairs[1],pairs[0])):
        k_ob=next((b for b in report.get("book_probes",[])
                   if b.get("venue")=="kalshi" and b.get("ticker")==left["kalshi_ticker"]),None)
        p_ob=next((b for b in report.get("book_probes",[])
                   if b.get("venue")=="polymarket" and str(b.get("token_id"))==str(right["polymarket_token_id"])),None)
        kp=k_ob.get("yes_buy_best_ask") if k_ob else None
        pp=p_ob.get("best_ask") if p_ob else None
        ip=indicative.get(str(right["polymarket_token_id"]))
        indicative_screen=None
        if kp is not None and ip is not None:
            try:
                indicative_screen=str(Decimal(str(kp))+ip)
            except (InvalidOperation,ValueError): pass
        result.append({"kalshi_team":left["team"],
            "kalshi_ticker":left["kalshi_ticker"],"kalshi_side":"YES",
            "polymarket_team":right["team"],
            "polymarket_token_id":right["polymarket_token_id"],
            "kalshi_best_displayed_ask":kp,
            "polymarket_best_displayed_ask":pp,
            "polymarket_gamma_indicative_price":str(ip) if ip is not None else None,
            "indicative_pair_cost_per_contract_before_fees":indicative_screen,
            "indicative_screen_only_not_executable":True,
            "status":"PRICE_EVIDENCE_INCOMPLETE" if kp is None or pp is None
                   else "TOP_OF_BOOK_ONLY_NO_DEPTH_OR_FEE_VALIDATION",
            "net_roi_verified":False,"paper_trade_allowed":False})
    return {"research_only":True,"status":"PAIR_CANDIDATES_NOT_VALIDATED",
            "total_budget_usd":"100","minimum_net_roi_pct":"greater_than_zero_after_all_costs",
            "combinations":result,"net_roi_verified":False,
            "reason":"Gamma prices are indicative, not executable asks; indicative sums do not establish depth, synchronization, fees, rules or net profit."}

if __name__=="__main__":
    r=json.loads(Path("one_event_book_probe.json").read_text(encoding="utf-8"))
    out=combinations(r)
    Path("one_event_pair_combinations.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_combinations":len(out["combinations"]),
                      "status":out["status"],"net_roi_verified":False}))
