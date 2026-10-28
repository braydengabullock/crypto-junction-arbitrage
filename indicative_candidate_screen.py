"""Screen snapshot title candidates using indicative prices only.

No order-book quotes, verified payouts, net returns, or trading signals.
"""
import argparse, json
from pathlib import Path
from decimal import Decimal, InvalidOperation
from one_event_outcome_pairs import outcomes

def screen(matches,poly_snapshot):
    by_id={str(m.get("id")):m for m in poly_snapshot.get("markets",[])}
    rows=[]
    for match in matches.get("candidates",[]):
        market=by_id.get(str(match.get("polymarket_id")))
        if not market: continue
        labels=outcomes(market.get("outcomes"))
        prices=outcomes(market.get("outcomePrices"))
        if len(labels)!=2 or len(prices)!=2: continue
        for label,price in zip(labels,prices):
            try:
                value=Decimal(str(price))
                if not value.is_finite() or not 0<=value<=1: continue
            except (InvalidOperation,ValueError,TypeError): continue
            rows.append({"kalshi_ticker":match.get("kalshi_ticker"),
                         "kalshi_title":match.get("kalshi_title"),
                         "polymarket_id":market.get("id"),
                         "polymarket_question":market.get("question"),
                         "polymarket_outcome":label,
                         "gamma_indicative_price":str(value),
                         "title_similarity":match.get("title_similarity"),
                         "classification":"UNVERIFIED_TITLE_CANDIDATE",
                         "opposing_outcome_verified":False,
                         "executable_price_verified":False,
                         "net_roi_verified":False})
    return {"research_only":True,"status":"INDICATIVE_DISCOVERY_ONLY",
            "candidate_outcomes":len(rows),"rows":rows,
            "warning":"These are title-overlap candidates, not matched outcomes. No Kalshi ask or fee-adjusted ROI is calculated. Manual rules and outcome mapping required."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--matches",required=True)
    p.add_argument("--polymarket",required=True)
    p.add_argument("--output",default="indicative_candidate_screen.json")
    a=p.parse_args()
    result=screen(json.loads(Path(a.matches).read_text()),
                  json.loads(Path(a.polymarket).read_text()))
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({"outcomes_screened":result["candidate_outcomes"],
                      "validated_opportunities":0,"research_only":True}))
if __name__=="__main__": main()
