"""Create the two opposite-side research combinations without inventing quotes.

Prices are NOT calculated from Gamma outcomePrices, since those are indicative.
"""
import json
from pathlib import Path

def combinations(report):
    pairs=report.get("exact_outcome_candidates",[])
    if len(pairs)!=2 or len({p.get("team") for p in pairs})!=2:
        return {"research_only":True,"status":"NO_EXACT_TWO_OUTCOME_PAIR",
                "combinations":[],"net_roi_verified":False}
    result=[]
    for left,right in ((pairs[0],pairs[1]),(pairs[1],pairs[0])):
        k_ob=next((b for b in report.get("book_probes",[])
                   if b.get("venue")=="kalshi" and b.get("ticker")==left["kalshi_ticker"]),None)
        p_ob=next((b for b in report.get("book_probes",[])
                   if b.get("venue")=="polymarket" and str(b.get("token_id"))==str(right["polymarket_token_id"])),None)
        kp=k_ob.get("yes_buy_best_ask") if k_ob else None
        pp=p_ob.get("best_ask") if p_ob else None
        result.append({"kalshi_team":left["team"],
            "kalshi_ticker":left["kalshi_ticker"],"kalshi_side":"YES",
            "polymarket_team":right["team"],
            "polymarket_token_id":right["polymarket_token_id"],
            "kalshi_best_displayed_ask":kp,
            "polymarket_best_displayed_ask":pp,
            "status":"PRICE_EVIDENCE_INCOMPLETE" if kp is None or pp is None
                   else "TOP_OF_BOOK_ONLY_NO_DEPTH_OR_FEE_VALIDATION",
            "net_roi_verified":False,"paper_trade_allowed":False})
    return {"research_only":True,"status":"PAIR_CANDIDATES_NOT_VALIDATED",
            "total_budget_usd":"100","minimum_net_roi_pct":"2",
            "combinations":result,"net_roi_verified":False,
            "reason":"Top-of-book prices are insufficient to validate $100 depth, fees, rules or synchronized fills."}

if __name__=="__main__":
    r=json.loads(Path("one_event_book_probe.json").read_text(encoding="utf-8"))
    out=combinations(r)
    Path("one_event_pair_combinations.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_combinations":len(out["combinations"]),
                      "status":out["status"],"net_roi_verified":False}))
