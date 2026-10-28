"""Public, read-only order-book capture and hypothetical $100 depth costing.

No account access, order placement, fees inference, or cross-venue match claims.
Kalshi publishes YES/NO bids; a BUY YES is inferred from NO bids and vice versa.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote
import json

def number(x):
    n=Decimal(str(x))
    if not n.is_finite() or n<0: raise ValueError("Invalid price or quantity")
    return n

def book_levels(entries):
    levels=[]
    for item in entries:
        if not isinstance(item,(list,tuple)) or len(item)!=2:
            raise ValueError("Invalid bid level")
        price,qty=map(number,item)
        if price>1: raise ValueError("Invalid binary price")
        if qty>0: levels.append((price,qty))
    return levels

def kalshi_buy_levels(orderbook, side):
    """Convert opposing bids into implied buy asks; do not assume top-of-book depth."""
    if side not in ("YES","NO"): raise ValueError("Side must be YES or NO")
    data=orderbook.get("orderbook_fp")
    if not isinstance(data,dict): raise ValueError("Missing fractional orderbook")
    opposing="no_dollars" if side=="YES" else "yes_dollars"
    bids=book_levels(data.get(opposing,[]))
    return sorted([(Decimal("1")-price,qty) for price,qty in bids],key=lambda x:x[0])

def polymarket_buy_levels(orderbook):
    asks=orderbook.get("asks")
    if not isinstance(asks,list): raise ValueError("Missing ask levels")
    levels=[]
    for entry in asks:
        price,qty=number(entry["price"]),number(entry["size"])
        if price>1: raise ValueError("Invalid binary price")
        if qty>0: levels.append((price,qty))
    return sorted(levels,key=lambda x:x[0])

def depth_cost(levels, contracts):
    """Conservative displayed-depth cost; NO indication of actual fills."""
    qty=number(contracts)
    if qty!=qty.to_integral_value() or qty<=0: raise ValueError("Positive whole contracts required")
    remaining=qty;cost=Decimal("0")
    for price,available in levels:
        filled=min(remaining,available)
        cost+=price*filled
        remaining-=filled
        if remaining==0: break
    return {"depth_sufficient":remaining==0,
            "displayed_cost_usd":str(cost) if remaining==0 else None,
            "unfilled_contracts":str(remaining)}

def fetch_kalshi_book(ticker, opener=urlopen):
    if not ticker or "/" in ticker or "?" in ticker: raise ValueError("Invalid ticker")
    url="https://api.elections.kalshi.com/trade-api/v2/markets/"+quote(ticker,safe="")+"/orderbook"
    with opener(Request(url,headers={"Accept":"application/json"}),timeout=20) as response:
        return json.load(response)

def fetch_polymarket_book(token_id, opener=urlopen):
    if not str(token_id).isdigit(): raise ValueError("Numeric token ID required")
    url="https://clob.polymarket.com/book?"+urlencode({"token_id":str(token_id)})
    with opener(Request(url,headers={"Accept":"application/json","User-Agent":"CryptoJunctionResearch/1.0"}),timeout=20) as response:
        return json.load(response)

def research_capture(*,kalshi_ticker,polymarket_token_id,opener=urlopen):
    k=fetch_kalshi_book(kalshi_ticker,opener=opener)
    kt=datetime.now(timezone.utc).isoformat()
    p=fetch_polymarket_book(polymarket_token_id,opener=opener)
    pt=datetime.now(timezone.utc).isoformat()
    return {
      "research_only":True,"executable_pair_verified":False,
      "rules_equivalence_verified":False,"trading_eligibility_verified":False,
      "source_a":"kalshi_public","source_b":"polymarket_clob_public",
      "kalshi_ticker":kalshi_ticker,"polymarket_token_id":str(polymarket_token_id),
      "kalshi_observed_at":kt,"polymarket_observed_at":pt,
      "kalshi_book":k,"polymarket_book":p,
      "warning":"Non-atomic sequential observations. Indicative book depth can vanish; fees, FX, settlement and eligibility unverified. No trade signal."
    }

def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description="Manual public orderbook capture; research only")
    parser.add_argument("--kalshi-ticker",required=True)
    parser.add_argument("--polymarket-token-id",required=True)
    parser.add_argument("--output",default="local_orderbook_research.json")
    args=parser.parse_args()
    data=research_capture(kalshi_ticker=args.kalshi_ticker,
                          polymarket_token_id=args.polymarket_token_id)
    Path(args.output).write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(json.dumps({"research_only":True,"executable_pair_verified":False,
                      "output":args.output,"note":"No trade opportunity validated."}))
if __name__=="__main__":
    main()
