"""Read-only live Kalshi smoke check; no trading, no notifications."""
import json
import sys
from kalshi_public import fetch_markets, snapshot

def main():
    markets=fetch_markets(limit=5)
    if not markets:
        raise RuntimeError("Kalshi returned no open markets")
    first=markets[0]
    if not isinstance(first,dict) or not isinstance(first.get("ticker"),str) or not first["ticker"]:
        raise RuntimeError("Unexpected Kalshi market schema")
    report=snapshot(markets)
    print(json.dumps({
        "result": "OK",
        "source":report["source"],
        "observed_at":report["observed_at"],
        "market_count":len(markets),
        "first_ticker":first["ticker"],
        "first_market_status":first.get("status"),
        "research_only":True,
        "trade_alerts_enabled":False,
    },indent=2))
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"LIVE CONNECTIVITY FAILED: {type(exc).__name__}: {exc}",file=sys.stderr)
        sys.exit(1)
