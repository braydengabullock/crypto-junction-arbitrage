"""Read-only Polymarket public Gamma market discovery.

Research ONLY: no wallet, credentials, order execution or claims of geographic
trading eligibility. Gamma indicative prices are not executable CLOB asks.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://gamma-api.polymarket.com/markets"

def fetch_markets(*, limit=100, max_pages=5, opener=urlopen):
    if not 1 <= limit <= 500 or not 1 <= max_pages <= 20:
        raise ValueError("Invalid pagination limit")
    markets = []
    for page in range(max_pages):
        query = urlencode({"active":"true","closed":"false",
                           "limit":limit,"offset":page*limit})
        request = Request(BASE + "?" + query,
                          headers={"Accept":"application/json",
                                   "User-Agent":"CJ-Arbitrage-Research/0.1"})
        with opener(request,timeout=20) as response:
            records = json.load(response)
        if not isinstance(records,list):
            raise ValueError("Unexpected Polymarket market response")
        markets.extend(records)
        if len(records) < limit:
            return markets, {"complete":True,"pages_fetched":page+1}
    return markets, {"complete":False,"pages_fetched":max_pages}

def snapshot(markets, pagination, *, now=None):
    return {
        "source":"polymarket_gamma_public",
        "observed_at":(now or datetime.now(timezone.utc)).isoformat(),
        "research_only":True,
        "data_quality":{
            "kind":"indicative_market_metadata_not_executable_orderbook",
            "depth_verified":False,
            "settlement_equivalence_verified":False,
            "trading_eligibility_verified":False,
            "pagination":pagination,
            "market_count":len(markets)
        },
        "markets":[{
            "id":m.get("id"),"question":m.get("question"),
            "conditionId":m.get("conditionId"),"slug":m.get("slug"),
            "description":m.get("description"),
            "resolutionSource":m.get("resolutionSource"),
            "endDate":m.get("endDate"),"active":m.get("active"),
            "closed":m.get("closed"),"outcomes":m.get("outcomes"),
            "outcomePrices":m.get("outcomePrices"),
            "clobTokenIds":m.get("clobTokenIds"),
            "liquidity":m.get("liquidity"),"volume":m.get("volume")
        } for m in markets]
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--limit",type=int,default=100)
    parser.add_argument("--max-pages",type=int,default=5)
    parser.add_argument("--output-dir",default="snapshots")
    args=parser.parse_args()
    markets,pagination=fetch_markets(limit=args.limit,max_pages=args.max_pages)
    result=snapshot(markets,pagination)
    folder=Path(args.output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    filename=folder/("polymarket_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+".json")
    filename.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"snapshot":str(filename),
                      "market_count":len(markets),
                      "complete":pagination["complete"],
                      "note":"Research only; not tradable arbitrage."}))
if __name__=="__main__":
    main()
