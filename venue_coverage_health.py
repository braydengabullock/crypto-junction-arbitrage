"""Read-only venue coverage health for archived public orderbook snapshots."""
import argparse
import json
from pathlib import Path


def inspect(archive_dir):
    files = sorted(Path(archive_dir).glob("*.json"))
    if not files:
        return {"status": "NO_SNAPSHOTS", "healthy": False, "snapshots": 0}
    total = {"kalshi": 0, "polymarket": 0}
    paired_rows = 0
    rows = 0
    snapshots = 0
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if doc.get("source_type") != "archived_public_orderbook_observations":
            continue
        for capture in doc.get("captures", []):
            snapshots += 1
            for row in capture.get("rows", []):
                venues = {obs.get("venue") for obs in row.get("observations", [])}
                rows += 1
                for venue in total:
                    total[venue] += int(venue in venues)
                paired_rows += int(all(v in venues for v in total))
    healthy = bool(snapshots and paired_rows)
    return {
        "status": "VENUE_COVERAGE_PRESENT" if healthy else "VENUE_COVERAGE_MISSING",
        "healthy": healthy, "snapshots": snapshots,
        "rows_with_observations": rows,
        "rows_with_both_venues": paired_rows,
        "venue_row_counts": total,
        "paired_row_fraction": round(paired_rows / rows, 4) if rows else 0,
        "warning": "Coverage is not proof of liquid, synchronized or settlement-equivalent quotes."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive_dir), indent=2))


if __name__ == "__main__":
    main()
