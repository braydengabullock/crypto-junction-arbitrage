"""Quantity sensitivity diagnostic tests."""
from unittest.mock import patch
from quantity_depth_fee_diagnostic import quantity_report


def test_quantity_sensitivity_and_funding_caps():
    rows = [{"kalshi_ticker": "GAME", "observations": [
        {"venue": "kalshi", "book": {}},
        {"venue": "polymarket", "token_id": "opp", "book": {}}]}]
    def cost(levels, n):
        return {"depth_sufficient": True, "displayed_cost_usd": str(n * levels[0][0])}
    with patch("quantity_depth_fee_diagnostic.kalshi_buy_levels", return_value=[(0.4, 120)]), \
         patch("quantity_depth_fee_diagnostic.polymarket_buy_levels", return_value=[(0.5, 120)]), \
         patch("quantity_depth_fee_diagnostic.depth_cost", side_effect=cost), \
         patch("quantity_depth_fee_diagnostic.kalshi_general_taker_fee", return_value=0), \
         patch("quantity_depth_fee_diagnostic.polymarket_sports_taker_fee", return_value=0):
        result = quantity_report(rows, {"GAME|YES": "opp"})
    assert result["trade_allowed"] is False
    item = result["scenarios"][0]
    assert [s["contracts_each"] for s in item["quantity_scenarios"]] == [1, 10, 100, 120]
    assert item["quantity_scenarios"][0]["modeled_net_usd"] == "-0.15"
    assert item["quantity_scenarios"][-1]["modeled_net_usd"] == "11.75"
    assert item["max_affordable_contracts_each"] == 120
