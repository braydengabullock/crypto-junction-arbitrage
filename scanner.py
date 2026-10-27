"""Research-only matched-YES/NO arbitrage evaluator. No live execution."""
from datetime import datetime, timezone
import csv
import json
import os
from pathlib import Path
import sqlite3
import urllib.request

ROOT = Path(__file__).resolve().parent

def dt(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return parsed.astimezone(timezone.utc)

def evaluate(row, cfg, now=None):
    now = now or datetime.now(timezone.utc)
    keys = ("event", "a_venue", "b_venue", "a_contract", "b_contract",
            "a_side", "b_side", "a_ask", "b_ask", "a_depth", "b_depth",
            "a_fee_per_contract", "b_fee_per_contract", "observed_at",
            "event_end_at", "expected_payout_at", "match_verified",
            "a_market_url", "b_market_url")
    missing = [key for key in keys if row.get(key) in (None, "")]
    if missing:
        return {"status": "REJECT", "reasons": ["missing " + k for k in missing]}
    try:
        a, b = float(row["a_ask"]), float(row["b_ask"])
        fee_a, fee_b = float(row["a_fee_per_contract"]), float(row["b_fee_per_contract"])
        depth_a, depth_b = float(row["a_depth"]), float(row["b_depth"])
        observed = dt(row["observed_at"])
        end = dt(row["event_end_at"])
        payout = dt(row["expected_payout_at"])
    except (ValueError, TypeError, OverflowError) as exc:
        return {"status": "REJECT", "reasons": ["invalid input: " + str(exc)]}

    issues = []
    if (row["a_side"].upper(), row["b_side"].upper()) not in (("YES", "NO"), ("NO", "YES")):
        issues.append("legs not complementary")
    if str(row["match_verified"]).lower() not in ("true", "yes", "1"):
        issues.append("settlement equivalence not verified")
    if row["a_venue"] == row["b_venue"] and row["a_contract"] == row["b_contract"]:
        issues.append("identical instrument on same venue")
    if not (0 <= a <= 1 and 0 <= b <= 1) or min(fee_a, fee_b, depth_a, depth_b) < 0:
        issues.append("invalid quote or depth")
    age = (now - observed).total_seconds()
    if age < -cfg["max_clock_skew_seconds"] or age > cfg["max_quote_age_seconds"]:
        issues.append("quote stale or clock mismatch")
    if end <= now:
        issues.append("event already ended")
    if payout <= now or (payout - now).total_seconds() > cfg["max_payout_hours"] * 3600:
        issues.append("payout not within target window")
    unit_cost = a + b + fee_a + fee_b
    count = 0 if unit_cost <= 0 else max(0, min(
        int(cfg["budget_usd"] / unit_cost), int(depth_a), int(depth_b)))
    if count == 0:
        issues.append("insufficient affordable matched depth")
    cost = count * unit_cost
    profit = count - cost
    roi = (profit / cost * 100) if cost else 0
    if roi < cfg["min_net_roi_pct"]:
        issues.append("below net ROI threshold")
    return {
        "status": "RESEARCH_PASS" if not issues else "REJECT",
        "reasons": issues,
        "event": row["event"],
        "contracts_each": count,
        "allocation_a": round(count * (a + fee_a), 2),
        "allocation_b": round(count * (b + fee_b), 2),
        "total_cost": round(cost, 2),
        "estimated_net_profit": round(profit, 2),
        "net_roi_pct": round(roi, 3),
        "observed_at": row["observed_at"],
        "expected_payout_at": row["expected_payout_at"],
        "a": {"venue": row["a_venue"], "contract": row["a_contract"], "side": row["a_side"],
              "ask": a, "url": row["a_market_url"]},
        "b": {"venue": row["b_venue"], "contract": row["b_contract"], "side": row["b_side"],
              "ask": b, "url": row["b_market_url"]},
    }

def telegram_text(result):
    if result["status"] != "RESEARCH_PASS":
        return None
    a, b = result["a"], result["b"]
    return (
        "CRYPTO JUNCTION — RESEARCH CANDIDATE, NOT A TRADE SIGNAL\n"
        f"{result['event']}\n"
        f"{a['venue']}: BUY {a['side']} {result['contracts_each']} x {a['contract']} "
        f"at up to ${a['ask']:.2f}\n{a['url']}\n"
        f"{b['venue']}: BUY {b['side']} {result['contracts_each']} x {b['contract']} "
        f"at up to ${b['ask']:.2f}\n{b['url']}\n"
        f"Capital ${result['total_cost']:.2f}; estimated net ${result['estimated_net_profit']:.2f} "
        f"({result['net_roi_pct']:.2f}%)\n"
        f"Observed: {result['observed_at']}; expected payout: {result['expected_payout_at']}\n"
        "DO NOT TRADE FROM THIS ALERT. Reverify asks, depth, fees, FX, terms, access and fill risk."
    )

def run(csv_path=None, telegram=False):
    cfg = json.loads((ROOT / "config.json").read_text())
    path = Path(csv_path) if csv_path else ROOT / "candidates.csv"
    db_path = ROOT / "research.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS scans (timestamp TEXT, event TEXT, status TEXT, details TEXT)")
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                result = evaluate(row, cfg)
                print(json.dumps(result, indent=2))
                db.execute("INSERT INTO scans VALUES (?, ?, ?, ?)",
                    (datetime.now(timezone.utc).isoformat(), row.get("event", ""),
                     result["status"], json.dumps(result)))
                alert = telegram_text(result)
                if telegram and alert:
                    token = os.getenv("CJ_TELEGRAM_BOT_TOKEN")
                    chat = os.getenv("CJ_TELEGRAM_CHAT_ID")
                    if token and chat:
                        data = json.dumps({"chat_id": chat, "text": alert}).encode()
                        req = urllib.request.Request(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            data=data, headers={"Content-Type": "application/json"})
                        with urllib.request.urlopen(req, timeout=15):
                            pass

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--file")
    p.add_argument("--telegram", action="store_true", help="Research labels only")
    opts = p.parse_args()
    run(opts.file, opts.telegram)
