"""Capture read-only Kalshi sports game-winner series, not random broad-market pages."""
import json
from datetime import datetime,timezone
from pathlib import Path
from kalshi_public import fetch_market_pages,snapshot

SERIES=("KXNBAGAME","KXNFLGAME","KXNHLGAME","KXMLBGAME","KXWNBAGAME")

def capture_sports(*,fetch=fetch_market_pages,series=SERIES):
    rows=[]; outcomes={}
    for ticker in series:
        try:
            markets,paging=fetch(page_size=100,max_pages=3,series_ticker=ticker)
            rows.extend(markets)
            outcomes[ticker]={"market_count":len(markets),"pages":paging}
        except (ValueError,TimeoutError,OSError) as exc:
            outcomes[ticker]={"error":type(exc).__name__}
    result=snapshot(rows)
    result["data_quality"]={"kind":"public_top_of_book_indicative",
        "depth_verified":False,"series_results":outcomes,
        "all_series_complete":all("error" not in x and x["pages"]["complete"] for x in outcomes.values())}
    return result

if __name__=="__main__":
    result=capture_sports()
    Path("kalshi_sports_snapshot.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"sports_markets":len(result["markets"]),
                      "series":result["data_quality"]["series_results"]}))
