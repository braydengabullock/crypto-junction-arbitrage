"""Near-miss replay reporting remains research-only."""
from historical_snapshot_replay import replay


def test_nonpositive_near_misses_preserved(monkeypatch):
    import historical_snapshot_replay as module
    def fake_screen(*args, **kwargs):
        return {"rows": [], "mapped_pairs_priced": 1,
                "pricing_diagnostics": {"PRICED_AT_LEAST_ONE_SIDE": 1},
                "near_misses": [{"kalshi_ticker": "TEST", "kalshi_side": "YES",
                                 "polymarket_token_id": "poly",
                                 "scenario": {"hypothetical_net_usd": "-0.15",
                                              "hypothetical_roi_pct": "-1.5",
                                              "total_cost_usd": "10.15",
                                              "contracts_each": 10,
                                              "minimum_total_cost_reduction_to_positive_usd": "0.16"},
                                 "quote_quality": {"within_20_seconds": True}}]}
    monkeypatch.setattr(module, "screen", fake_screen)
    archive={"source_type":"archived_public_orderbook_observations",
             "trade_allowed":False,
             "captures":[{"captured_at":"2026-11-01T00:00:00+00:00",
                          "rows":[], "opposing_token_map":{}}]}
    result=replay(archive)
    assert result["total_positive_candidate_observations"] == 0
    assert result["closest_nonpositive_near_misses"][0]["modeled_net_usd"] == "-0.15"
    assert result["captures"][0]["closest_nonpositive_near_misses"][0]["minimum_total_cost_reduction_to_positive_usd"] == "0.16"
    assert result["closest_nonpositive_near_misses"][0]["settlement_rules_verified"] is False
