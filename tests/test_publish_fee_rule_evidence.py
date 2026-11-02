from publish_fee_rule_evidence import build


def test_missing_fee_and_rules_are_reported_per_unique_pair():
    archive = {"captures": [
        {"opposing_token_map": {"K|YES": "P", "K|NO": "Q"}},
        {"opposing_token_map": {"K|YES": "P"}}]}
    result = build(archive)
    assert result["pairs_examined"] == 2
    assert result["pairs_with_complete_evidence"] == 0
    assert result["pairs_verified_executable"] == 0
    assert all(x["status"] == "EVIDENCE_INCOMPLETE" for x in result["records"])
    assert result["trade_allowed"] is False
