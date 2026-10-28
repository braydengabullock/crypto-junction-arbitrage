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
    """Sample both active trading and upcoming resolution windows.

    The two sorted samples may overlap. Deduplicate by market ID so our
    coverage count is honest; this is still not exhaustive discovery.
    """
    if not 1 <= limit <= 100 or not 1 <= max_pages <= 20:
        raise ValueError("Invalid pagination limit")
    markets, seen = [], set()
    plans = [("volume24hr", False, (max_pages + 1)//2),
             ("endDate", True, max_pages//2)]
    details = []
    all_complete = True
    for order, ascending, pages in plans:
        complete = False
        visited = 0
        for page in range(pages):
            query = urlencode({"active":"true","closed":"false",
                               "limit":limit,"offset":page*limit,
                               "order":order,
                               "ascending":str(ascending).lower()})
            request = Request(BASE + "?" + query,
                              headers={"Accept":"application/json",
                                       "User-Agent":"CJ-Arbitrage-Research/0.1"})
            with opener(request, timeout=20) as response:
                records = json.load(response)
            if not isinstance(records,list):
                raise ValueError("Unexpected Polymarket market response")
            visited += 1
            for record in records:
                ident = record.get("id")
                if ident is not None and str(ident) in seen:
                    continue
                if ident is not None:
                    seen.add(str(ident))
                markets.append(record)
            if len(records) < limit:
                complete = True
                break
        if pages:
            all_complete = all_complete and complete
        details.append({"order":order,"ascending":ascending,
                        "pages_fetched":visited,"complete":complete})
    return markets, {"complete":all_complete,
                     "pages_fetched":sum(x["pages_fetched"] for x in details),
                     "sorts":details,"deduplicated":True,
                     "coverage":"mixed active-volume and earliest-end-date samples"}

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
