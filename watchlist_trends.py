"""Compare read-only near-miss watchlists across captures, without trading."""
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

def compare(previous,current):
    def index(doc):
        result={}
        for r in doc.get("watchlist",[]):
            key=(str(r.get("kalshi_ticker")),str(r.get("kalshi_side")),str(r.get("polymarket_token_id")))
            try:
                val=Decimal(str(r["illustrative_net_usd"]))
                if val.is_finite():result[key]=val
            except (KeyError,InvalidOperation,TypeError):continue
        return result
    old=index(previous);new=index(current)
    changes=[]
    for key,value in new.items():
        prior=old.get(key)
        changes.append({"kalshi_ticker":key[0],"kalshi_side":key[1],
            "polymarket_token_id":key[2],"previous_net_usd":str(prior) if prior is not None else None,
            "current_net_usd":str(value),
            "change_usd":str(value-prior) if prior is not None else None,
            "trend":"NEW" if prior is None else ("IMPROVING" if value>prior else "WORSENING" if value<prior else "UNCHANGED"),
            "research_only":True})
    counts={name:sum(x["trend"]==name for x in changes) for name in ("IMPROVING","WORSENING","UNCHANGED","NEW")}
    return {"research_only":True,"trade_allowed":False,"profit_verified":False,
            "trend_counts":counts,
            "comparable_pairs":sum(x["change_usd"] is not None for x in changes),
            "changes":changes,"warning":"Sequential snapshots are not simultaneous executable quotes."}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--previous",required=True)
    p.add_argument("--current",default="near_miss_watchlist.json")
    p.add_argument("--output",default="watchlist_trends.json")
    args=p.parse_args()
    out=compare(json.loads(Path(args.previous).read_text()),json.loads(Path(args.current).read_text()))
    Path(args.output).write_text(json.dumps(out,indent=2))
    print(json.dumps({"comparable_pairs":out["comparable_pairs"],"pairs_seen":len(out["changes"]),
                      "trend_counts":out["trend_counts"]}))
