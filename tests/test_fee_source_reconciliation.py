from fee_source_reconciliation import reconcile, build


def test_fee_api_value_is_not_mistaken_for_verified_rate():
    result = reconcile({"kalshi_market_id": "K", "polymarket_token_id": "123",
                        "polymarket_fee_api_raw": {"base_fee": 1000},
                        "polymarket_fee_schedule_metadata": {"rate": 0.05}})
    assert result["published_polymarket_sports_fee_rate_applied"] is False
    assert result["pricing_inputs_verified"] is False
    assert result["trade_allowed"] is False
    assert "POLYMARKET_BASE_FEE_SEMANTICS_UNVERIFIED" in result["issues"]


def test_missing_source_fields_fail_closed():
    report = build({"records": [{"kalshi_market_id": "K"}]})
    assert report["records_with_verified_two_venue_fee_inputs"] == 0
    assert "POLYMARKET_FEE_API_MISSING" in report["records"][0]["issues"]
