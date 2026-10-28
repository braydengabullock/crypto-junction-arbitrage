"""One-event read-only public orderbook paper comparison.

A human must independently inspect event rules and select a genuinely
complementary token. No order placement, alerts, or verified earnings.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from orderbook_research import fetch_kalshi_book, fetch_polymarket_book
from depth_pair_review import review

def now():
    return datetime.now(timezone.utc).isoformat()

def compare_one(*, ticker, token_id, kalshi_side, fee_kalshi, fee_polymarket,
                fetch_k=fetch_kalshi_book, fetch_p=fetch_polymarket_book):
    if kalshi_side not in ("YES","NO"):
        raise ValueError("Choose Kalshi YES or NO")
    if not str(token_id).isdigit():
        raise ValueError("Polymarket token ID must be numeric")
    ka=now()
    kb=fetch_k(ticker)
    kz=now()
    pa=now()
    pb=fetch_p(token_id)
    pz=now()
    result=review(kb,pb,kalshi_side=kalshi_side,observed_kalshi=kz,
                  observed_polymarket=pz,fee_kalshi=fee_kalshi,
                  fee_polymarket=fee_polymarket,budget="100")
    duration=(datetime.fromisoformat(pz)-datetime.fromisoformat(ka)).total_seconds()
    # Two non-atomic fetches: gate on the full uncertainty window.
    if duration>20 or duration<0:
        result["scenarios"]=[]
        result.pop("largest_displayed_scenario",None)
        result["reasons"].insert(0,"Full request window exceeds 20 seconds")
    return {"research_only":True,"ticker":ticker,"token_id":str(token_id),
            "kalshi_side":kalshi_side,"kalshi_fetch_started":ka,
            "kalshi_fetch_finished":kz,"polymarket_fetch_started":pa,
            "polymarket_fetch_finished":pz,"full_capture_seconds":duration,
            "paper_review":result,"matching_rules_verified":False,
            "outcome_complementarity_verified":False,
            "trading_eligibility_verified":False,
            "warning":"Human-supplied counterpart only. Confirm exact game, outcome, overtime, source, fees and settlement independently. No trading."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kalshi-ticker",required=True)
    p.add_argument("--polymarket-token-id",required=True)
    p.add_argument("--kalshi-side",choices=("YES","NO"),required=True)
    p.add_argument("--kalshi-fee-per-contract",required=True)
    p.add_argument("--polymarket-fee-per-contract",required=True)
    p.add_argument("--output",default="one_event_paper_review.json")
    a=p.parse_args()
    result=compare_one(ticker=a.kalshi_ticker,token_id=a.polymarket_token_id,
        kalshi_side=a.kalshi_side,fee_kalshi=a.kalshi_fee_per_contract,
        fee_polymarket=a.polymarket_fee_per_contract)
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"output":a.output,"research_only":True,
                      "scenarios":len(result["paper_review"]["scenarios"]),
                      "trade_allowed":False}))
if __name__=="__main__":
    main()
