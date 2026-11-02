"""Publish read-only quantity sensitivity for archived orderbook captures."""
import argparse
import json
from pathlib import Path
from quantity_depth_fee_diagnostic import quantity_report


def build(archive):
    captures = []
    for capture in archive.get("captures", []):
        report = quantity_report(capture.get("rows", []),
                                 capture.get("opposing_token_map", {}))
        captures.append({"captured_at": capture.get("captured_at"),
                         "scenarios": report["scenarios"]})
    return {"research_only": True, "trade_allowed": False,
            "settlement_rules_verified": False, "fee_inputs_verified": False,
            "capture_count": len(captures), "captures": captures,
            "warning": "Modeled costs only. No settlement equivalence, fills or actual fees verified."}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    archive = json.loads(Path(args.archive).read_text(encoding="utf-8"))
    result = build(archive)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"capture_count": result["capture_count"],
                      "quantity_scenarios": sum(len(x["scenarios"]) for x in result["captures"]),
                      "research_only": True}))


if __name__ == "__main__":
    main()
