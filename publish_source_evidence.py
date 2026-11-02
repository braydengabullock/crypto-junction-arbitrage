"""Bounded, read-only evidence collection for archived opposing market mappings."""
import argparse
import json
from pathlib import Path
from source_evidence_collection import collect_pair


def mapped_pairs(archive, limit=20):
    unique = {}
    for capture in archive.get("captures", []):
        for key, token in capture.get("opposing_token_map", {}).items():
            if not isinstance(key, str) or "|" not in key:
                continue
            ticker, side = key.rsplit("|", 1)
            if ticker and side in ("YES", "NO") and str(token).isdigit():
                unique[(ticker, str(token))] = None
    return list(unique)[:limit]


def build(archive, *, limit=20, collector=collect_pair):
    records = []
    for ticker, token in mapped_pairs(archive, limit):
        try:
            records.append(collector(ticker, token))
        except Exception as exc:
            records.append({"kalshi_market_id": ticker,
                            "polymarket_token_id": token,
                            "status": "SOURCE_EVIDENCE_INCOMPLETE",
                            "issues": ["Collector error: " + type(exc).__name__],
                            "trade_allowed": False,
                            "settlement_equivalence_verified": False})
    return {"research_only": True, "trade_allowed": False,
            "pairs_attempted": len(records), "records": records,
            "pairs_verified_executable": 0,
            "warning": "Source fields and fee metadata are not independent verification of fees or equivalent settlement."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error("limit must be between 1 and 20")
    report = build(json.loads(Path(args.archive).read_text(encoding="utf-8")), limit=args.limit)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"pairs_attempted": report["pairs_attempted"], "pairs_verified_executable": 0}))


if __name__ == "__main__":
    main()
