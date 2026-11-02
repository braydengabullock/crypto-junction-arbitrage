"""Read-only quantity sensitivity report for archived research observations.

Shows modeled 1/10/100/max-affordable quantities for each mapped opposing
outcome. Never places trades or verifies settlement equivalence.
"""
from decimal import Decimal
from orderbook_research import kalshi_buy_levels, polymarket_buy_levels, depth_cost
from fee_estimates import kalshi_general_taker_fee, polymarket_sports_taker_fee


def quantity_report(rows, mapping, *, poly_rate="0.05", kalshi_multiplier="1",
                    extra_cost="0.25", fx_cost="0", budget="5000",
                    per_venue_budget="2500"):
    output = []
    fixed = Decimal(extra_cost)
    fx = Decimal(fx_cost)
    combined_cap = min(Decimal(budget), Decimal("5000"))
    venue_cap = min(Decimal(per_venue_budget), Decimal("2500"))
    for row in rows:
        ko = next((x for x in row.get("observations", []) if x.get("venue") == "kalshi"), None)
        polys = [x for x in row.get("observations", []) if x.get("venue") == "polymarket"]
        if not ko:
            continue
        for side in ("YES", "NO"):
            token = mapping.get(str(row.get("kalshi_ticker")) + "|" + side)
            if not token:
                continue
            po = next((x for x in polys if str(x.get("token_id")) == str(token)), None)
            if not po:
                continue
            try:
                kl = kalshi_buy_levels(ko["book"], side)
                pl = polymarket_buy_levels(po["book"])
                if not kl or not pl:
                    continue
                depth_limit = min(int(sum(q for _, q in kl)), int(sum(q for _, q in pl)), 10000)
                scenarios = {}
                for n in range(1, depth_limit + 1):
                    kc, pc = depth_cost(kl, n), depth_cost(pl, n)
                    if not (kc["depth_sufficient"] and pc["depth_sufficient"]):
                        break
                    kcost = Decimal(kc["displayed_cost_usd"])
                    pcost = Decimal(pc["displayed_cost_usd"])
                    kfee = kalshi_general_taker_fee(n, kcost / n, multiplier=Decimal(kalshi_multiplier))
                    pfee = polymarket_sports_taker_fee(n, pcost / n, rate=Decimal(poly_rate))
                    total = kcost + pcost + kfee + pfee + fixed + fx
                    # Match conservative unknown-venue funding reserve in depth_fee_screen.
                    if (total > combined_cap or kcost + kfee + fixed + fx > venue_cap
                            or pcost + pfee + fixed + fx > venue_cap):
                        break
                    scenarios[n] = {
                        "contracts_each": n,
                        "kalshi_displayed_cost_usd": str(kcost),
                        "polymarket_displayed_cost_usd": str(pcost),
                        "kalshi_modeled_fee_usd": str(kfee),
                        "polymarket_modeled_fee_usd": str(pfee),
                        "fixed_and_fx_usd": str(fixed + fx),
                        "modeled_total_cost_usd": str(total),
                        "modeled_net_usd": str(Decimal(n) - total),
                        "modeled_roi_pct": str(((Decimal(n) - total) / total * 100).quantize(Decimal("0.001"))),
                    }
                if scenarios:
                    quantities = sorted(set((1, 10, 100, max(scenarios))))
                    output.append({
                        "kalshi_ticker": row.get("kalshi_ticker"),
                        "kalshi_side": side,
                        "polymarket_token_id": str(token),
                        "max_affordable_contracts_each": max(scenarios),
                        "depth_limit_contracts_each": depth_limit,
                        "quantity_scenarios": [scenarios[n] for n in quantities if n in scenarios],
                        "excluded_quantities": [n for n in (1, 10, 100) if n not in scenarios],
                        "settlement_rules_verified": False,
                        "fee_inputs_verified": False,
                        "trade_allowed": False,
                    })
            except (KeyError, ValueError, TypeError, ArithmeticError, ZeroDivisionError):
                continue
    return {"research_only": True, "trade_allowed": False,
            "fee_inputs_verified": False, "market_rules_verified": False,
            "fee_assumptions": {"polymarket_rate": str(poly_rate),
                                "kalshi_multiplier": str(kalshi_multiplier),
                                "fixed_cost_usd": str(fixed), "fx_cost_usd": str(fx)},
            "scenarios": output,
            "warning": "Indicative book depth and unverified fee inputs; not executable arbitrage."}
