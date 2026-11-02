"""Summarize missing fee and settlement evidence for archived mapped pairs.

Does not fetch official rules or assert that any pair is executable.
"""
import argparse
import json
from pathlib import Path
from fee_rule_evidence_gate import audit_candidate


def build(archive):
    unique = {}
    for capture in archive.get("captures", []):
        for key, token in capture.get("opposing_token_map", {}).items():
            if not isinstance(key, str) or "|" not in key:
                continue
            ticker, side = key.rsplit("|", 1)
            if not ticker or side not in ("YES", "NO") or not str(token).strip():
                continue
            identifier = (ticker, side, str(token))
            unique[identifier] = {
                "kalshi_market_id": ticker,
                "kalshi_side": side,
                "polymarket_market_id": str(token),
            }
    records = [audit_candidate(candidate) for candidate in unique.values()]
    return {"research_only": True, "trade_allowed": False,
            "pairs_examined": len(records),
            "pairs_with_complete_evidence": sum(not r["review_issues"] for r in records),
            "pairs_verified_executable": 0,
            "records": records,
            "warning": "This report tracks missing evidence only; official fee and rule sources must be collected and independently checked."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    archive = json.loads(Path(args.archive).read_text(encoding="utf-8"))
    report = build(archive)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("pairs_examined", "pairs_with_complete_evidence", "pairs_verified_executable")}))


if __name__ == "__main__":
    main()
