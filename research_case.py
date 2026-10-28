"""Fail-closed orchestration of a manual rules dossier and public orderbooks.

This is a NON-ACTIONABLE research report: user-supplied rule summaries and
displayed order books cannot establish executable arbitrage or account access.
"""
from rule_dossier import review_rules
from depth_pair_review import review as price_review

def evaluate_research_case(case):
    result = {
        "status": "BLOCKED",
        "research_only": True,
        "verified_arbitrage": False,
        "realized_profit_usd": None,
        "trade_allowed": False,
        "issues": [],
        "rule_review": None,
        "displayed_depth_review": None,
    }
    if not isinstance(case, dict):
        result["issues"].append("Case must be an object")
        return result
    a, b = case.get("rules_a"), case.get("rules_b")
    rules = review_rules(a, b)
    result["rule_review"] = rules
    if rules["status"] != "MANUAL_EVIDENCE_MATCH":
        result["issues"].extend(rules["reasons"])
        return result
    required = ("kalshi_book", "polymarket_book", "observed_kalshi",
                "observed_polymarket", "fee_kalshi", "fee_polymarket",
                "kalshi_side", "polymarket_side",
                "kalshi_ticker", "polymarket_token_id")
    missing = [key for key in required if case.get(key) is None or case.get(key) == ""]
    if missing:
        result["issues"].append("Missing: " + ", ".join(missing))
        return result
    if case["kalshi_side"] != a["selected_side"] or case["polymarket_side"] != b["selected_side"]:
        result["issues"].append("Orderbook sides do not match dossier sides")
        return result
    if not str(case["kalshi_ticker"]).strip() or not str(case["polymarket_token_id"]).strip():
        result["issues"].append("Explicit instrument identifiers required")
        return result
    prices = price_review(
        case["kalshi_book"], case["polymarket_book"],
        kalshi_side=case["kalshi_side"],
        observed_kalshi=case["observed_kalshi"],
        observed_polymarket=case["observed_polymarket"],
        fee_kalshi=case["fee_kalshi"],
        fee_polymarket=case["fee_polymarket"],
        budget="100",
    )
    result["displayed_depth_review"] = prices
    result["issues"].extend(prices["reasons"])
    result["status"] = "PAPER_CANDIDATE_REQUIRES_VERIFICATION" if prices["scenarios"] else "BLOCKED"
    return result
