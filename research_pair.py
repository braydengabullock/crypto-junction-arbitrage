"""Non-trading safety gates for manual prediction-market research.

Never infers legal eligibility, resolution equivalence or synchronized broker
quotes from similar names. No network calls.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from urllib.parse import urlparse

CENT = Decimal("0.01")

def D(value):
    return Decimal(str(value))

def utc(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Timezone required")
    return timestamp.astimezone(timezone.utc)

def assess_pair(pair, *, now=None, budget="100", threshold="2", horizon_minutes=120,
                max_age_seconds=20):
    now = now or datetime.now(timezone.utc)
    problems = []
    required = ("source_a", "source_b", "contract_a", "contract_b", "side_a",
                "side_b", "ask_a", "ask_b", "depth_a", "depth_b", "fee_a",
                "fee_b", "asof_a", "asof_b", "expected_payout_a",
                "expected_payout_b", "settlement_verified", "currency_a",
                "currency_b", "url_a", "url_b", "eligibility_verified")
    missing = [x for x in required if x not in pair or pair[x] is None or pair[x] == ""]
    if missing:
        return {"status": "BLOCKED", "reasons": ["Missing: " + ", ".join(missing)]}
    if pair["source_a"] == pair["source_b"]:
        problems.append("Two independent underlying venues required")
    if (str(pair["side_a"]).upper(), str(pair["side_b"]).upper()) not in (
        ("YES", "NO"), ("NO", "YES")
    ):
        problems.append("Not complementary YES/NO")
    if pair["settlement_verified"] is not True:
        problems.append("Independent resolution-rule verification required")
    if pair["eligibility_verified"] is not True:
        problems.append("Trading permissions not verified")
    if pair["currency_a"] != "USD" or pair["currency_b"] != "USD":
        problems.append("USD denomination/FX costs not verified")
    for k in ("url_a", "url_b"):
        u = urlparse(str(pair[k]))
        if u.scheme != "https" or not u.netloc:
            problems.append("No verified HTTPS contract link: " + k)
    try:
        a, b = D(pair["ask_a"]), D(pair["ask_b"])
        fa, fb = D(pair["fee_a"]), D(pair["fee_b"])
        da, db = int(pair["depth_a"]), int(pair["depth_b"])
        if any(not z.is_finite() for z in (a,b,fa,fb)) or any(
            z < 0 for z in (a,b,fa,fb)
        ) or a > 1 or b > 1 or min(da,db) < 0:
            raise ValueError("Invalid price/fee/depth")
        times = [utc(pair[k]) for k in (
            "asof_a","asof_b","expected_payout_a","expected_payout_b")]
        for stamp in times[:2]:
            if not (-5 <= (now-stamp).total_seconds() <= max_age_seconds):
                problems.append("Missing synchronized fresh executable quotes")
                break
        for stamp in times[2:]:
            if not (now < stamp <= now.replace(year=now.year) +
                    __import__("datetime").timedelta(minutes=horizon_minutes)):
                problems.append("Payout outside 2-hour target")
                break
        cost_each = a+b+fa+fb
        n = min(da,db,int((D(budget)/cost_each).to_integral_value(rounding=ROUND_DOWN))) if cost_each > 0 else 0
        if n < 1:
            problems.append("Insufficient depth or budget")
        spent = n*cost_each
        net = D(n)-spent
        roi = (net/spent*100) if spent else D(0)
        if roi < D(threshold):
            problems.append("Net ROI below minimum")
    except (ValueError, InvalidOperation, OverflowError, TypeError) as exc:
        return {"status":"BLOCKED","reasons":problems+[str(exc)]}
    result = {
        "status": "RESEARCH_REVIEW" if not problems else "BLOCKED",
        "reasons": problems,
        "contracts_each": n,
        "capital_usd": str(spent.quantize(CENT)),
        "allocation_a_usd": str((n*(a+fa)).quantize(CENT)),
        "allocation_b_usd": str((n*(b+fb)).quantize(CENT)),
        "estimated_net_usd": str(net.quantize(CENT)),
        "estimated_net_roi_pct": str(roi.quantize(Decimal("0.001"))),
        "url_a": pair["url_a"], "url_b": pair["url_b"],
        "warning": "Research only. Recheck both asks, depth, fees, settlement rules, eligibility and unmatched-leg risk.",
    }
    return result

def format_research_alert(pair, result):
    if result["status"] != "RESEARCH_REVIEW":
        return None
    return (
        "CRYPTO JUNCTION — RESEARCH REVIEW ONLY (NOT A TRADE SIGNAL)\n"
        f"{pair['contract_a']} / {pair['contract_b']}\n"
        f"{pair['source_a']}: BUY {pair['side_a']} — {result['contracts_each']} @ max ${pair['ask_a']}\n"
        f"{result['url_a']}\n"
        f"{pair['source_b']}: BUY {pair['side_b']} — {result['contracts_each']} @ max ${pair['ask_b']}\n"
        f"{result['url_b']}\n"
        f"Total: ${result['capital_usd']} USD | Estimated net: ${result['estimated_net_usd']} "
        f"({result['estimated_net_roi_pct']}%)\n"
        "Must manually verify broker prices and BOTH fills; legs cannot be atomic."
    )
