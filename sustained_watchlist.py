"""Conservative research-only watchlist momentum filter.

Requires repeated fixed-size improvement across three consecutive snapshots.
"""
import json
from pathlib import Path
from decimal import Decimal,InvalidOperation

def sustained(oldest,previous,current):
    def idx(doc):
        out={}
        for r in doc.get("watchlist",[]):
            key=(str(r.get("kalshi_ticker")),str(r.get("kalshi_side")),str(r.get("polymarket_token_id")))
            v=r.get("fixed_ten_contract_pairs") or {}
            if v.get("contracts_each")!=10:continue
            try:
                p=Decimal(str(v["hypothetical_net_usd"]))
                if p.is_finite():out[key]=p
            except (KeyError,ValueError,TypeError,InvalidOperation):pass
        return out
    a,b,c=map(idx,(oldest,previous,current));result=[]
    for key,now in c.items():
        if key not in a or key not in b:continue
        trend="TWO_CONSECUTIVE_IMPROVEMENTS" if a[key]<b[key]<now else "NOT_SUSTAINED"
        result.append({"kalshi_ticker":key[0],"kalshi_side":key[1],
            "polymarket_token_id":key[2],"fixed_ten_net_usd":[str(a[key]),str(b[key]),str(now)],
            "trend":trend,"research_only":True,"trade_allowed":False})
    return {"research_only":True,"trade_allowed":False,"profit_verified":False,
            "three_run_comparisons":len(result),
            "sustained_improvements":sum(x["trend"]=="TWO_CONSECUTIVE_IMPROVEMENTS" for x in result),
            "rows":result}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    for key in ("oldest","previous","current"):p.add_argument("--"+key,required=True)
    p.add_argument("--output",default="sustained_watchlist.json")
    a=p.parse_args()
    r=sustained(*(json.loads(Path(getattr(a,key)).read_text()) for key in ("oldest","previous","current")))
    Path(a.output).write_text(json.dumps(r,indent=2))
    print(json.dumps({"three_run_comparisons":r["three_run_comparisons"],"sustained_improvements":r["sustained_improvements"]}))
