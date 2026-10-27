"""Read-only Kalshi public market discovery. Does not create arbitrage signals.

Usage:
    python kalshi_public.py --limit 30
    python kalshi_public.py --limit 30 --event-ticker EVENT_TICKER
The output is a local JSON snapshot, never a trading alert.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
ROOT = Path(__file__).resolve().parent

def fetch_markets(limit=30, event_ticker=None, opener=urlopen):
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    params = {"limit": limit, "status": "open"}
    if event_ticker:
        params["event_ticker"] = event_ticker
    url = BASE_URL + "/markets?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "CJ-Arbitrage-Research/0.3", "Accept": "application/json"})
    with opener(req, timeout=20) as response:
        obj = json.load(response)
    if not isinstance(obj, dict) or not isinstance(obj.get("markets"), list):
        raise ValueError("Unrecognized Kalshi response")
    return obj["markets"]


def fetch_market_pages(*, page_size=100, max_pages=5, event_ticker=None, opener=urlopen):
    """Bounded, read-only cursor pagination. Reports whether coverage is complete."""
    if not 1 <= page_size <= 100 or not 1 <= max_pages <= 20:
        raise ValueError("Invalid page size or page cap")
    rows, seen_cursors, cursor = [], set(), None
    for _ in range(max_pages):
        params = {"limit": page_size, "status": "open"}
        if event_ticker:
            params["event_ticker"] = event_ticker
        if cursor:
            params["cursor"] = cursor
        req = Request(BASE_URL + "/markets?" + urlencode(params),
                      headers={"User-Agent": "CJ-Arbitrage-Research/0.4",
                               "Accept": "application/json"})
        with opener(req, timeout=20) as response:
            obj = json.load(response)
        if not isinstance(obj, dict) or not isinstance(obj.get("markets"), list):
            raise ValueError("Unrecognized Kalshi paginated response")
        rows.extend(obj["markets"])
        next_cursor = obj.get("cursor")
        if not next_cursor:
            return rows, {"complete": True, "pages_fetched": len(seen_cursors)+1}
        if not isinstance(next_cursor, str) or next_cursor in seen_cursors:
            raise ValueError("Invalid or repeated Kalshi pagination cursor")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return rows, {"complete": False, "pages_fetched": max_pages}

def snapshot(markets, now=None):
    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    return {
        "source": "kalshi_public",
        "observed_at": timestamp,
        "research_only": True,
        "markets": [
            {
                "ticker": m.get("ticker"),
                "event_ticker": m.get("event_ticker"),
                "title": m.get("title"),
                "subtitle": m.get("subtitle"),
                "status": m.get("status"),
                "close_time": m.get("close_time"),
                "expiration_time": m.get("expiration_time"),
                "yes_bid_dollars": m.get("yes_bid_dollars"),
                "yes_ask_dollars": m.get("yes_ask_dollars"),
                "no_bid_dollars": m.get("no_bid_dollars"),
                "no_ask_dollars": m.get("no_ask_dollars"),
                "volume_fp": m.get("volume_fp"),
                "rules_primary": m.get("rules_primary"),
            }
            for m in markets
        ],
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--event-ticker")
    p.add_argument("--output", default="kalshi_snapshot.json")
    args = p.parse_args()
    output = ROOT / args.output
    if output.resolve().parent != ROOT.resolve():
        raise ValueError("Output must stay in project directory")
    markets = fetch_markets(args.limit, args.event_ticker)
    output.write_text(json.dumps(snapshot(markets), indent=2), encoding="utf-8")
    print(f"Saved {len(markets)} public Kalshi markets to {output.name} (RESEARCH ONLY).")
    print("No cross-exchange matches verified; no trade alerts or live orders.")

if __name__ == "__main__":
    main()
