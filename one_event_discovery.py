"""Focused public API probe for one game, with NO trade execution.

Records factual API evidence and failures. Never assumes identical settlement.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

KALSHI_EVENT = "KXNBAGAME-26OCT28OKCDAL"
POLY_SLUG = "nba-okc-dal-2026-10-28"

def probe(*, opener=urlopen):
    urls={
      "kalshi_event":"https://api.elections.kalshi.com/trade-api/v2/events/"+quote(KALSHI_EVENT,safe=""),
      "polymarket_event":"https://gamma-api.polymarket.com/events/slug/"+quote(POLY_SLUG,safe="")
    }
    result={"research_only":True,"event":"2026-10-28 Oklahoma City Thunder vs Dallas Mavericks",
            "captured_at":datetime.now(timezone.utc).isoformat(),
            "rule_equivalence_verified":False,"orderbook_depth_verified":False,
            "sources":{},"errors":[]}
    for name,url in urls.items():
        try:
            req=Request(url,headers={"Accept":"application/json","User-Agent":"CJ-Arbitrage-Research/0.5"})
            with opener(req,timeout=20) as response:
                data=json.load(response)
            if not isinstance(data,dict):
                raise ValueError("Unexpected event payload")
            result["sources"][name]={"url":url,"data":data}
        except HTTPError as e:
            result["errors"].append({"source":name,"http_status":e.code,"type":"HTTPError"})
        except (URLError,ValueError,TimeoutError) as e:
            result["errors"].append({"source":name,"type":type(e).__name__})
    return result

if __name__=="__main__":
    result=probe()
    Path("one_event_discovery.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"sources_returned":list(result["sources"]),
                      "errors":result["errors"],"research_only":True}))
