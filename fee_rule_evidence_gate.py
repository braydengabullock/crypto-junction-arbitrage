"""Fail-closed fee and settlement evidence gate for research candidates.

No market may be labeled execution-ready by this module.
Published category defaults are not proof of market-specific fees.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

REQUIRED_RULE_FIELDS = ("event_identity", "outcome_definition", "overtime",
                        "tie_handling", "postponement", "cancellation",
                        "abandonment", "forfeit", "resolution_source",
                        "determination_time", "settlement_currency", "payout_amount")


def _valid_rate(value):
    try:
        rate = Decimal(str(value))
        return rate.is_finite() and Decimal("0") <= rate <= Decimal("1")
    except (InvalidOperation, TypeError, ValueError):
        return False


def audit_candidate(candidate, *, kalshi_fee=None, polymarket_fee=None,
                    kalshi_rules=None, polymarket_rules=None):
    """Classify missing evidence; never certify a trade or infer rules from titles."""
    issues = []
    for venue, fee in (("kalshi", kalshi_fee), ("polymarket", polymarket_fee)):
        if not isinstance(fee, dict):
            issues.append(venue + ": fee evidence missing")
            continue
        if not _valid_rate(fee.get("rate_or_multiplier")):
            issues.append(venue + ": invalid fee input")
        if fee.get("market_id") != candidate.get(venue + "_market_id"):
            issues.append(venue + ": fee evidence market mismatch")
        if not str(fee.get("official_source_url", "")).startswith("https://"):
            issues.append(venue + ": official fee source missing")
        if not fee.get("effective_at_utc"):
            issues.append(venue + ": fee effective time missing")
        else:
            try:
                dt = datetime.fromisoformat(str(fee["effective_at_utc"]).replace("Z", "+00:00"))
                if dt.tzinfo is None or dt.astimezone(timezone.utc) > datetime.now(timezone.utc):
                    issues.append(venue + ": invalid/future fee effective time")
            except (ValueError, TypeError):
                issues.append(venue + ": invalid fee effective time")
        if fee.get("independently_checked") is not True:
            issues.append(venue + ": fee schedule not independently checked")
    for venue, rules in (("kalshi", kalshi_rules), ("polymarket", polymarket_rules)):
        if not isinstance(rules, dict):
            issues.append(venue + ": settlement rules missing")
            continue
        if rules.get("market_id") != candidate.get(venue + "_market_id"):
            issues.append(venue + ": rule evidence market mismatch")
        if not str(rules.get("official_rule_url", "")).startswith("https://"):
            issues.append(venue + ": official settlement rules link missing")
        missing = [field for field in REQUIRED_RULE_FIELDS if not str(rules.get(field) or "").strip()]
        if missing:
            issues.append(venue + ": missing rule fields: " + ", ".join(missing))
        if rules.get("independently_checked") is not True:
            issues.append(venue + ": rules not independently reviewed")
    return {
        "candidate": candidate,
        "fee_evidence_complete": not any("fee" in x for x in issues),
        "rule_evidence_complete": not any("rule" in x for x in issues),
        "review_issues": issues,
        "status": "EVIDENCE_INCOMPLETE" if issues else "MANUAL_COMPARISON_REQUIRED",
        "settlement_equivalence_verified": False,
        "fees_verified_for_execution": False,
        "trade_allowed": False,
        "warning": "Evidence completeness is not cross-venue rule equivalence or executable profitability."
    }
