"""Explain whether raw price gaps or modeled trading friction limit mapped pairs."""
import argparse
import json
from decimal import Decimal,InvalidOperation
from pathlib import Path
from collections import defaultdict

def diagnose(data):
    rows=[]
    for item in data.get("near_misses",[]):
        f=item.get("fixed_ten_contract_pairs")
        if not f: continue
        try:
            raw=Decimal(str(f["raw_displayed_spread_usd"]))
            friction=Decimal(str(f["modeled_total_friction_usd"]))
            net=Decimal(str(f["hypothetical_net_usd"]))
        except (KeyError,InvalidOperation,TypeError,ValueError):
            continue
        if not all(x.is_finite() for x in (raw,friction,net)): continue
        rows.append({"kalshi_ticker":item.get("kalshi_ticker"),"kalshi_side":item.get("kalshi_side"),
                     "polymarket_token_id":item.get("polymarket_token_id"),
                     "raw_displayed_spread_usd":str(raw),
                     "modeled_total_friction_usd":str(friction),
                     "illustrative_net_usd":str(net),
                     "economics_category":"RAW_SPREAD_NONPOSITIVE" if raw<=0 else
                        ("FRICTION_ERASES_SPREAD" if net<=0 else "POSITIVE_ILLUSTRATIVE_UNVERIFIED"),
                     "quote_quality":item.get("quote_quality",{})})
    league_groups=defaultdict(list)
    for row in rows:
        ticker=str(row.get("kalshi_ticker") or "")
        league=ticker.split("GAME-",1)[0].removeprefix("KX") if "GAME-" in ticker else "OTHER"
        league_groups[league].append(row)
    by_league={}
    for league,group in sorted(league_groups.items()):
        by_league[league]={
            "pairs":len(group),
            "positive_raw_spread_pairs":sum(Decimal(x["raw_displayed_spread_usd"])>0 for x in group),
            "positive_illustrative_net_pairs":sum(Decimal(x["illustrative_net_usd"])>0 for x in group),
            "best_raw_spread_usd":str(max(Decimal(x["raw_displayed_spread_usd"]) for x in group)),
            "best_illustrative_net_usd":str(max(Decimal(x["illustrative_net_usd"]) for x in group)),
            "mean_raw_spread_usd":str(sum(Decimal(x["raw_displayed_spread_usd"]) for x in group)/len(group)),
        }
    counts={category:sum(x["economics_category"]==category for x in rows)
            for category in ("RAW_SPREAD_NONPOSITIVE","FRICTION_ERASES_SPREAD","POSITIVE_ILLUSTRATIVE_UNVERIFIED")}
    return {"research_only":True,"trade_allowed":False,"verified_opportunities":0,
            "fixed_ten_pairs_analyzed":len(rows),"counts":counts,"by_league":by_league,"rows":rows,
            "warning":"Fee assumptions, settlement equivalence and execution unverified. Categories describe only modeled fixed-ten economics."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="depth_fee_illustrative.json")
    p.add_argument("--output",default="opportunity_economics.json")
    a=p.parse_args()
    result=diagnose(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"fixed_ten_pairs_analyzed":result["fixed_ten_pairs_analyzed"],"counts":result["counts"],"by_league":result["by_league"]}))
if __name__=="__main__":
    main()
