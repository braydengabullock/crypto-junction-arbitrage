"""Capture time-stamped public Kalshi quotes for future historical analysis.

Data are indicative exchange-level quotes, not Wealthsimple execution prices.
No order-book depth, matched ForecastEx leg, or executable arbitrage implied.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from kalshi_public import fetch_markets, snapshot

def capture(*, limit=100, event_ticker=None, output_dir="snapshots"):
    markets=fetch_markets(limit=limit,event_ticker=event_ticker)
    observed=datetime.now(timezone.utc)
    payload=snapshot(markets,now=observed)
    payload["data_quality"]={
        "kind":"public_top_of_book_indicative",
        "depth_verified":False,
        "wealthsimple_executability_verified":False,
        "forecast_ex_match_verified":False,
        "coverage":"only first requested API page; not all open Kalshi markets",
        "requested_limit":limit,
        "market_count":len(markets),
    }
    folder=Path(output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    name="kalshi_"+observed.strftime("%Y%m%dT%H%M%SZ")+".json"
    path=folder/name
    path.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(json.dumps({"snapshot":str(path),"observed_at":payload["observed_at"],
                      "market_count":len(markets),"data_quality":payload["data_quality"]},indent=2))
    return path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--limit",type=int,default=100)
    p.add_argument("--event-ticker")
    p.add_argument("--output-dir",default="snapshots")
    a=p.parse_args()
    capture(limit=a.limit,event_ticker=a.event_ticker,output_dir=a.output_dir)

if __name__=="__main__":
    main()
