"""Conservative research readiness report for two public market snapshots.

Never represents candidate counts as viable arbitrages or profits.
"""
import argparse
import json
from pathlib import Path
from market_comparison import compare, read_snapshot

def readiness(kalshi, polymarket, *, threshold=0.55):
    matches,total=compare(kalshi,polymarket,threshold=threshold)
    kp=kalshi.get("data_quality",{}).get("pagination",{})
    pp=polymarket.get("data_quality",{}).get("pagination",{})
    return {
        "status":"RESEARCH_ONLY",
        "kalshi_market_count":len(kalshi["markets"]),
        "polymarket_market_count":len(polymarket["markets"]),
        "title_match_candidates":total,
        "candidates_retained":len(matches),
        "verified_rule_matches":0,
        "validated_executable_opportunities":0,
        "verified_profitable_trades":0,
        "actual_realized_profit_usd":None,
        "snapshot_times":{"kalshi":kalshi.get("observed_at"),
                          "polymarket":polymarket.get("observed_at")},
        "coverage":{"kalshi_complete":kp.get("complete"),
                    "polymarket_complete":pp.get("complete")},
        "backtest_ready":False,
        "blocking_gaps":[
            "Independently verified settlement and resolution equivalence",
            "Synchronized historical executable orderbook asks and depth for both sides",
            "Complete fees, slippage, FX and platform trading eligibility",
            "Authenticated historical fills and verified settlement payouts",
            "Capital reuse timing and sampling-bias analysis"
        ],
        "warning":"A title match is not arbitrage. Counts are research leads only; no profitability claims."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kalshi",required=True)
    p.add_argument("--polymarket",required=True)
    p.add_argument("--output",default="readiness_report.json")
    args=p.parse_args()
    k=read_snapshot(args.kalshi,"kalshi_public")
    poly=read_snapshot(args.polymarket,"polymarket_gamma_public")
    result=readiness(k,poly)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
