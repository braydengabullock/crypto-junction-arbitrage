"""Diagnose CLOB public read access with one authorized public token.

No retries, alternate routes, proxies, authentication, or order submission.
"""
import json
from datetime import datetime,timezone
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from pathlib import Path
from candidate_orderbooks import parse_tokens

def inspect(snapshot, *, opener=urlopen, sports_token=None):
    markets=snapshot.get("markets",[])
    selected=next(((m,t) for m in markets if m.get("enableOrderBook") is not False
                   and m.get("acceptingOrders") is not False
                   for t in parse_tokens(m.get("clobTokenIds"))[:1]),None)
    result={"research_only":True,"captured_at":datetime.now(timezone.utc).isoformat(),
            "diagnostic_only":True,"requests":[],"access_conclusion":"NO_VALID_TOKEN",
            "trading_enabled":False}
    if selected is None:return result
    market,token=selected
    result["token_id"]=token
    result["control_market_id"]=market.get("id")
    result["market_id"]=market.get("id")
    for endpoint,params in (("book",{"token_id":token}),("price",{"token_id":token,"side":"BUY"})):
        url="https://clob.polymarket.com/"+endpoint+"?"+urlencode(params)
        req=Request(url,headers={"Accept":"application/json","User-Agent":"CryptoJunctionResearch/1.0"})
        entry={"endpoint":endpoint,"http_status":None,"response_kind":None}
        try:
            with opener(req,timeout=12) as response:
                payload=json.load(response)
                entry["http_status"]=getattr(response,"status",200)
                entry["response_kind"]="json_object" if isinstance(payload,dict) else "json_other"
        except HTTPError as exc:
            entry["http_status"]=exc.code
            entry["response_kind"]="http_denied" if exc.code==403 else "http_error"
        except (URLError,TimeoutError,ValueError,OSError) as exc:
            entry["response_kind"]=type(exc).__name__
        result["requests"].append(entry)
    statuses=[r["http_status"] for r in result["requests"]]
    if statuses==[403,403]:
        result["access_conclusion"]="CLOB_HOST_REFUSES_BOTH_PUBLIC_READ_ENDPOINTS"
    elif statuses[0]==403:
        result["access_conclusion"]="BOOK_ACCESS_REFUSED"
    elif statuses[0]==200:
        result["access_conclusion"]="BOOK_PUBLIC_READ_ACCESSIBLE"
    else:
        result["access_conclusion"]="UNDETERMINED"
    if sports_token is not None and str(sports_token).isdigit():
        url="https://clob.polymarket.com/book?"+urlencode({"token_id":str(sports_token)})
        req=Request(url,headers={"Accept":"application/json","User-Agent":"CryptoJunctionResearch/1.0"})
        entry={"endpoint":"book","token_id":str(sports_token),"http_status":None,"response_kind":None}
        try:
            with opener(req,timeout=12) as response:
                payload=json.load(response)
                entry["http_status"]=getattr(response,"status",200)
                entry["response_kind"]="json_object" if isinstance(payload,dict) else "json_other"
        except HTTPError as exc:
            entry["http_status"]=exc.code
            entry["response_kind"]="http_denied" if exc.code==403 else "http_error"
        except (URLError,TimeoutError,ValueError,OSError) as exc:
            entry["response_kind"]=type(exc).__name__
        result["sports_token_probe"]=entry
        if result["requests"][0]["http_status"]==200 and entry["http_status"]==403:
            result["access_conclusion"]="CONTROL_ACCESSIBLE_SPORTS_TOKEN_REFUSED"
    return result

if __name__=="__main__":
    files=sorted(Path("snapshots").glob("polymarket_*.json"))
    if not files: raise SystemExit("No Polymarket snapshot available")
    sport_token=None
    matches=Path("research_matches.json")
    if matches.exists():
        candidates=json.loads(matches.read_text(encoding="utf-8")).get("candidates",[])
        for item in candidates:
            if item.get("match_method")=="sports_identifier_date_teams_research":
                tokens=parse_tokens(item.get("polymarket_clob_token_ids"))
                if tokens:
                    sport_token=tokens[0]
                    break
    out=inspect(json.loads(files[-1].read_text(encoding="utf-8")),sports_token=sport_token)
    Path("clob_access_diagnostic.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"conclusion":out["access_conclusion"],"requests":out["requests"],
                      "research_only":True}))
