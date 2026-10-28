"""First real-data research test report; no verified arbitrage or realized returns."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

def report(matches, quality):
    if matches.get("research_only") is not True or quality.get("research_only") is not True:
        raise ValueError("Only research-only source reports accepted")
    rows=quality.get("details",[])
    return {
        "phase":"PHASE_1_REAL_MARKET_OBSERVATION",
        "created_at":datetime.now(timezone.utc).isoformat(),
        "research_only":True,
        "title_match_candidates":matches.get("potential_title_matches_found",0),
        "orderbook_candidates_sampled":quality.get("rows_examined",0),
        "paired_books_collected":quality.get("rows_with_kalshi_and_polymarket_books",0),
        "timestamp_aligned_candidates":quality.get("rows_with_synchronized_observations",0),
        "displayed_depth_on_both_venues":quality.get("rows_with_displayed_depth_on_both_venues",0),
        "api_errors":quality.get("request_errors",0),
        "verified_trade_opportunities":0,
        "actual_profit_usd":None,
        "projected_net_profit_usd":None,
        "paper_trades_executed":0,
        "limitations":[
            "No validated equivalent contract rules",
            "Books are sequential public snapshots, not executable quotes",
            "No verified costs, legal access or actual matched fills",
            "No settlement observations establishing final P&L"
        ],
        "sampled_instruments":[{"kalshi":r.get("kalshi_ticker"),
                                "polymarket":r.get("polymarket_id"),
                                "both_books":r.get("both_books"),
                                "synchronized":r.get("synchronized"),
                                "depth":r.get("displayed_depth_on_both")} for r in rows],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--matches",required=True)
    p.add_argument("--quality",required=True)
    p.add_argument("--output",default="phase1_real_data_report.json")
    a=p.parse_args()
    results=report(json.loads(Path(a.matches).read_text(encoding="utf-8")),
                   json.loads(Path(a.quality).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps(results,indent=2))
if __name__=="__main__":
    main()
