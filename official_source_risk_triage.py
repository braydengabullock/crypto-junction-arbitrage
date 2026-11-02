"""Read-only triage of primary-source contract text and fee metadata.

Differences are review flags, not semantic determinations. A matching keyword
pattern cannot establish equivalent settlement or a verified executable fee.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

TOPICS = {
    "overtime": r"\bovertime\b|\bextra time\b|\bregulation\b",
    "postponement": r"\bpostpon(?:ed|ement|e)\b|\breschedul(?:ed|ing|e)\b",
    "cancellation": r"\bcancell?(?:ed|ation)?\b|\bvoid(?:ed)?\b",
    "forfeit": r"\bforfeit(?:ed|ure)?\b",
    "tie": r"\btie\b|\bdraw\b",
    "abandonment": r"\babandon(?:ed|ment)?\b",
    "fair_price": r"\bfair.price\b|\b50\s*[-/]\s*50\b",
}


def assess(record):
    kalshi = " ".join(str(record.get(field) or "") for field in
                     ("kalshi_rules_primary", "kalshi_rules_secondary"))
    polymarket = str(record.get("polymarket_description") or "")
    flags = []
    if not kalshi.strip() or not polymarket.strip():
        flags.append("MISSING_RULE_TEXT")
    for topic, pattern in TOPICS.items():
        if bool(re.search(pattern, kalshi, re.I)) != bool(re.search(pattern, polymarket, re.I)):
            flags.append("TEXT_MENTION_DIFFERENCE_" + topic.upper())
    if (re.search(r"48\s*hours?", kalshi, re.I)
            and re.search(r"postpon|reschedul", kalshi, re.I)
            and re.search(r"postpon|reschedul", polymarket, re.I)
            and not re.search(r"48\s*hours?", polymarket, re.I)):
        flags.append("POSSIBLE_POSTPONEMENT_WINDOW_MISMATCH")
    fee = record.get("polymarket_fee_api_raw")
    if not isinstance(fee, dict) or "base_fee" not in fee:
        flags.append("POLYMARKET_FEE_API_VALUE_MISSING")
    else:
        flags.append("POLYMARKET_BASE_FEE_UNIT_AND_FORMULA_UNVERIFIED")
    if record.get("polymarket_fee_schedule_metadata") is None:
        flags.append("POLYMARKET_FEE_SCHEDULE_METADATA_MISSING")
    flags.append("KALSHI_MARKET_SPECIFIC_FEE_NOT_VERIFIED")
    return {"kalshi_market_id": record.get("kalshi_market_id"),
            "polymarket_token_id": record.get("polymarket_token_id"),
            "flags": sorted(set(flags)),
            "status": "MANUAL_REVIEW_REQUIRED",
            "trade_allowed": False,
            "settlement_equivalence_verified": False,
            "fee_inputs_verified": False}


def build(source_report):
    records = [assess(r) for r in source_report.get("records", [])]
    counts = Counter(flag for r in records for flag in r["flags"])
    return {"research_only": True, "trade_allowed": False,
            "records_examined": len(records),
            "flag_counts": dict(sorted(counts.items())),
            "records": records,
            "warning": "Fee API values are not automatically converted to trade fees. Rule keyword differences are triage hints only; human source review remains necessary."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build(json.loads(Path(args.input).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"records_examined": result["records_examined"],
                      "flag_counts": result["flag_counts"]}))


if __name__ == "__main__":
    main()
