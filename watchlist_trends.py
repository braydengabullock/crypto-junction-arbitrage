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
                fixed=r.get("fixed_ten_contract_pairs") or {}
                fixed_profit=Decimal(str(fixed["hypothetical_net_usd"])) if fixed.get("contracts_each")==10 else None
                quality=r.get("quote_quality") or {}
                quality_ok=(quality.get("both_books_present") is True and quality.get("within_20_seconds") is True and quality.get("sufficient_depth_for_ten") is True)
                if val.is_finite():result[key]=(val,qty,fixed_profit,quality_ok)
            except (KeyError,InvalidOperation,TypeError):continue
        return result
    old=index(previous);new=index(current)
    changes=[]
    for key,value in new.items():
        prior=old.get(key)
        old_profit=prior[0] if prior is not None else None
        old_qty=prior[1] if prior is not None else None
        new_profit,new_qty,new_fixed,quality_ok=value
        old_fixed=prior[2] if prior is not None else None
        benchmark_comparable=(old_fixed is not None and new_fixed is not None)
        same_size=old_qty==new_qty and new_qty>0 if prior is not None else False
        priority=("APPROACHING_BREAK_EVEN" if quality_ok and benchmark_comparable and new_fixed>old_fixed and new_fixed<0 and new_fixed>=Decimal("-0.25") else
                  "POSITIVE_ILLUSTRATIVE_REQUIRES_VERIFICATION" if quality_ok and new_fixed is not None and new_fixed>0 else
                  "MONITOR_ONLY")
        previous_streak=0
        if prior is not None:
            for old_row in previous.get("changes",[]):
                if (str(old_row.get("kalshi_ticker")),str(old_row.get("kalshi_side")),str(old_row.get("polymarket_token_id")))==key:
                    previous_streak=int(old_row.get("near_break_even_streak",0)) if old_row.get("near_break_even_streak",0) is not None else 0
                    break
        close_now=new_fixed is not None and Decimal("-0.25")<=new_fixed<0
        streak=(min(previous_streak,10000)+1) if close_now else 0
        changes.append({"near_break_even_streak":streak,"monitoring_priority":priority,
            "distance_to_break_even_fixed_ten_usd":str(-new_fixed) if new_fixed is not None and new_fixed<0 else "0" if new_fixed is not None else None,"kalshi_ticker":key[0],"kalshi_side":key[1],
            "polymarket_token_id":key[2],"previous_net_usd":str(old_profit) if prior is not None else None,
            "current_net_usd":str(new_profit),
            "previous_contracts_each":old_qty,"current_contracts_each":new_qty,
            "same_position_size":same_size,
            "fixed_ten_previous_net_usd":str(old_fixed) if old_fixed is not None else None,
            "fixed_ten_current_net_usd":str(new_fixed) if new_fixed is not None else None,
            "fixed_ten_change_usd":str(new_fixed-old_fixed) if benchmark_comparable else None,
            "fixed_ten_trend":("UNAVAILABLE" if not benchmark_comparable else "IMPROVING" if new_fixed>old_fixed else "WORSENING" if new_fixed<old_fixed else "UNCHANGED"),
            "change_usd":str(new_profit-old_profit) if same_size else None,
            "trend":"NEW" if prior is None else "SIZE_CHANGED_NOT_COMPARABLE" if not same_size else ("IMPROVING" if new_profit>old_profit else "WORSENING" if new_profit<old_profit else "UNCHANGED"),
            "research_only":True})
    counts={name:sum(x["trend"]==name for x in changes) for name in ("IMPROVING","WORSENING","UNCHANGED","NEW","SIZE_CHANGED_NOT_COMPARABLE")}
    priority_counts={name:sum(x["monitoring_priority"]==name for x in changes) for name in ("APPROACHING_BREAK_EVEN","POSITIVE_ILLUSTRATIVE_REQUIRES_VERIFICATION","MONITOR_ONLY")}
    benchmark_counts={name:sum(x["fixed_ten_trend"]==name for x in changes) for name in ("IMPROVING","WORSENING","UNCHANGED","UNAVAILABLE")}
    ranked=sorted(changes,key=lambda x:(not x["quote_quality_passed"],x["distance_to_break_even_fixed_ten_usd"] is None,
        Decimal(x["distance_to_break_even_fixed_ten_usd"]) if x["distance_to_break_even_fixed_ten_usd"] is not None else Decimal("999999")))
    return {"research_only":True,"trade_allowed":False,"profit_verified":False,
            "closest_fixed_ten_pairs":ranked[:5],
            "near_break_even_streak_note":"Streak requires previous comparison report with changes; ordinary watchlist input resets history.",
            "fixed_ten_trend_counts":benchmark_counts,
            "monitoring_priority_counts":priority_counts,
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
                      "trend_counts":out["trend_counts"],
                      "fixed_ten_trend_counts":out["fixed_ten_trend_counts"],
                      "monitoring_priority_counts":out["monitoring_priority_counts"]}))
