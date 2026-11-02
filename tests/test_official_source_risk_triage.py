from official_source_risk_triage import assess, build


def test_postponement_mismatch_is_flagged():
    row = {"kalshi_market_id": "K", "polymarket_token_id": "123",
           "kalshi_rules_primary": "If postponed more than 48 hours settle at fair price",
           "polymarket_description": "If postponed wait for rescheduled game",
           "polymarket_fee_api_raw": {"base_fee": 1000},
           "polymarket_fee_schedule_metadata": {"rate": 0.05}}
    result = assess(row)
    assert "POSSIBLE_POSTPONEMENT_WINDOW_MISMATCH" in result["flags"]
    assert result["trade_allowed"] is False
    assert result["fee_inputs_verified"] is False


def test_missing_rules_and_fee_stay_blocked():
    result = build({"records": [{"kalshi_market_id": "K", "polymarket_token_id": "123"}]})
    assert result["records_examined"] == 1
    assert "MISSING_RULE_TEXT" in result["records"][0]["flags"]
    assert "POLYMARKET_FEE_API_VALUE_MISSING" in result["records"][0]["flags"]
    assert result["trade_allowed"] is False
