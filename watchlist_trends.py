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
                qty=int(r.get("contracts_each",0))
                if val.is_finite():result[key]=(val,qty)
            except (KeyError,InvalidOperation,TypeError):continue
        return result
    old=index(previous);new=index(current)
    changes=[]
    for key,value in new.items():
        prior=old.get(key)
        old_profit=prior[0] if prior is not None else None
        old_qty=prior[1] if prior is not None else None
        new_profit,new_qty=value
        same_size=old_qty==new_qty and new_qty>0 if prior is not None else False
        changes.append({"kalshi_ticker":key[0],"kalshi_side":key[1],
            "polymarket_token_id":key[2],"previous_net_usd":str(old_profit) if prior is not None else None,
            "current_net_usd":str(new_profit),
            "previous_contracts_each":old_qty,"current_contracts_each":new_qty,
            "same_position_size":same_size,
            "change_usd":str(new_profit-old_profit) if same_size else None,
            "trend":"NEW" if prior is None else "SIZE_CHANGED_NOT_COMPARABLE" if not same_size else ("IMPROVING" if new_profit>old_profit else "WORSENING" if new_profit<old_profit else "UNCHANGED"),
            "research_only":True})
    counts={name:sum(x["trend"]==name for x in changes) for name in ("IMPROVING","WORSENING","UNCHANGED","NEW","SIZE_CHANGED_NOT_COMPARABLE")}
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
