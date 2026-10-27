"""Offline-only opportunity review pipeline.

Takes one candidate plus manually entered balances. No API calls, no Telegram,
no trading. Candidates are NOT a verified source of broker executable quotes.
"""
import json
import argparse
from pathlib import Path
from research_pair import assess_pair, format_research_alert
from capital_limits import capital_check

def review(candidate, balances, *, now=None):
    pair = assess_pair(candidate, now=now)
    if pair["status"] != "RESEARCH_REVIEW":
        return {"status": "BLOCKED", "reasons": pair["reasons"], "pair": pair}
    required = ("balance_a", "balance_b", "portfolio_total", "total_current_committed")
    if any(field not in balances for field in required):
        return {"status": "BLOCKED", "reasons": ["Missing independently entered balances"], "pair": pair}
    capital = capital_check(pair, **{k: balances[k] for k in required})
    if not capital["allowed"]:
        return {"status": "BLOCKED", "reasons": capital["reasons"], "pair": pair}
    return {
        "status": "PAPER_REVIEW",
        "reasons": [],
        "pair": pair,
        "capital": capital,
        "message_preview": format_research_alert(candidate, pair),
        "warning": "Synthetic/manual inputs; never actionable without authorized live broker quotes and settlement checks.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True, help="Offline candidate JSON path")
    p.add_argument("--balances", required=True, help="Manually entered balance JSON path")
    args = p.parse_args()
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    balances = json.loads(Path(args.balances).read_text(encoding="utf-8"))
    print(json.dumps(review(candidate, balances), indent=2))
if __name__ == "__main__":
    main()
