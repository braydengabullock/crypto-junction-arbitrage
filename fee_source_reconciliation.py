"""Conservative per-token fee source reconciliation; never enables trading.

The official Polymarket sports rate is 0.05, but a market must be identified as
sports by source metadata. Kalshi market-specific multipliers are not supplied
by the existing collector, so complete two-venue verification stays blocked.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def reconcile(record):
    metadata = record.get("polymarket_fee_schedule_metadata")
    fee_api = record.get("polymarket_fee_api_raw")
    issues = []
    # The CLOB base_fee integer has no established conversion to the published
    # feeRate in the collected evidence. Never silently interpret it.
    if not isinstance(fee_api, dict) or "base_fee" not in fee_api:
        issues.append("POLYMARKET_FEE_API_MISSING")
    else:
        issues.append("POLYMARKET_BASE_FEE_SEMANTICS_UNVERIFIED")
    if metadata is None:
        issues.append("POLYMARKET_SCHEDULE_MISSING")
    else:
        issues.append("POLYMARKET_SCHEDULE_CLASSIFICATION_NOT_INDEPENDENTLY_VERIFIED")
    issues.append("KALSHI_SERIES_MULTIPLIER_AND_EFFECTIVE_SCHEDULE_UNVERIFIED")
    return {"kalshi_market_id": record.get("kalshi_market_id"),
            "polymarket_token_id": record.get("polymarket_token_id"),
            "polymarket_fee_api_raw": fee_api,
            "polymarket_fee_schedule_metadata": metadata,
            "published_polymarket_sports_fee_rate_reference": "0.05",
            "published_polymarket_sports_fee_rate_applied": False,
            "pricing_inputs_verified": False,
            "trade_allowed": False,
            "issues": issues}

def build(report):
    records = [reconcile(x) for x in report.get("records", [])]
    return {"research_only": True, "trade_allowed": False,
            "records_examined": len(records),
            "records_with_verified_two_venue_fee_inputs": 0,
            "issue_counts": dict(sorted(Counter(i for r in records for i in r["issues"]).items())),
            "records": records,
            "reference": "https://docs.polymarket.com/trading/fees",
            "warning": "A published category rate is not a market-specific verified execution fee; existing hypothetical screen rates remain unchanged."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build(json.loads(Path(args.input).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"records_examined": result["records_examined"],
                      "verified": result["records_with_verified_two_venue_fee_inputs"]}))

if __name__ == "__main__":
    main()
