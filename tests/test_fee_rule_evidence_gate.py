from fee_rule_evidence_gate import audit_candidate


def test_missing_evidence_blocks_candidate():
    result = audit_candidate({"kalshi_market_id": "K", "polymarket_market_id": "P"})
    assert result["status"] == "EVIDENCE_INCOMPLETE"
    assert result["trade_allowed"] is False
    assert result["settlement_equivalence_verified"] is False
    assert len(result["review_issues"]) == 4


def test_category_default_without_source_does_not_verify_fee():
    candidate = {"kalshi_market_id": "K", "polymarket_market_id": "P"}
    fee = {"market_id": "K", "rate_or_multiplier": "1",
           "effective_at_utc": "2026-10-01T00:00:00Z", "independently_checked": True}
    result = audit_candidate(candidate, kalshi_fee=fee)
    assert any("official fee source missing" in issue for issue in result["review_issues"])
    assert result["fees_verified_for_execution"] is False
