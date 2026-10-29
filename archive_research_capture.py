"""Package one real research run's observed orderbooks for future offline replay.

This does not synthesize data, backfill history, verify outcomes or trade.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

def build(books, mapping):
    if not isinstance(books,dict) or not isinstance(books.get("rows"),list):
        raise ValueError("Invalid captured orderbook report")
    if not isinstance(mapping,dict) or mapping.get("mapping_method")!="exact_event_id_and_two_unambiguous_outcome_labels" or mapping.get("market_rules_verified") is not False:
        raise ValueError("Unverified explicit outcome map required")
    observed_at=books.get("captured_at")
    if not observed_at:
        raise ValueError("Missing snapshot collection timestamp")
    dt=datetime.fromisoformat(str(observed_at).replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("Snapshot timestamp must contain timezone")
    # Only retain actual recorded observations; never represent synthetic/missing books as collected.
    rows=[]
    for item in books["rows"]:
        if not isinstance(item,dict): continue
        obs=[x for x in item.get("observations",[]) if isinstance(x,dict) and isinstance(x.get("book"),dict)
             and x.get("venue") in ("kalshi","polymarket") and x.get("observed_at") and x.get("request_started_at")]
        if not obs: continue
        rows.append({"kalshi_ticker":item.get("kalshi_ticker"),"observations":obs,"errors":item.get("errors",[])})
    snapshot={"captured_at":dt.astimezone(timezone.utc).isoformat(),
              "rows":rows,"opposing_token_map":mapping.get("opposing_token_map",{})}
    return {"source_type":"archived_public_orderbook_observations",
            "research_only":True,"trade_allowed":False,
            "provenance_note":"Observed public books and rule-unverified explicit outcome labels from this GitHub Actions run; not historical backfill.",
            "captures":[snapshot],"books_with_observations":len(rows),
            "market_rules_verified":False,"net_profit_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--books",default="candidate_orderbooks.json")
    p.add_argument("--mapping",default="opposing_token_map.json")
    p.add_argument("--output",default="historical_capture_archive.json")
    args=p.parse_args()
    data=build(json.loads(Path(args.books).read_text(encoding="utf-8")),
               json.loads(Path(args.mapping).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(json.dumps({"captured_at":data["captures"][0]["captured_at"],
                      "books_with_observations":data["books_with_observations"],
                      "historical_backfill":False,"research_only":True}))
if __name__=="__main__":
    main()
