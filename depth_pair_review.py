"""Research-only cross-exchange displayed-depth scenarios; no execution or alerts."""
from datetime import datetime, timezone
from decimal import Decimal
from orderbook_research import kalshi_buy_levels, polymarket_buy_levels, depth_cost

def _date(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result.astimezone(timezone.utc)

def review(kalshi_book, polymarket_book, *, kalshi_side, observed_kalshi,
           observed_polymarket, fee_kalshi=None, fee_polymarket=None,
           budget="100", max_lag_seconds=20):
    """Caller supplies opposite outcome Polymarket token; equivalence is NOT verified."""
    result={"status":"RESEARCH_ONLY","validated_opportunity":False,
            "trade_allowed":False,"reasons":[],"scenarios":[]}
    try:
        if kalshi_side not in ("YES","NO"):
            raise ValueError("Invalid Kalshi side")
        if fee_kalshi is None or fee_polymarket is None:
            raise ValueError("Explicit per-contract fees required")
        fk,fp=Decimal(str(fee_kalshi)),Decimal(str(fee_polymarket))
        cap=Decimal(str(budget))
        if any(not x.is_finite() or x<0 for x in (fk,fp,cap)) or cap>100:
            raise ValueError("Invalid fees or $100 ceiling")
        if abs((_date(observed_kalshi)-_date(observed_polymarket)).total_seconds())>max_lag_seconds:
            raise ValueError("Non-synchronized observations")
        k=kalshi_buy_levels(kalshi_book,kalshi_side)
        p=polymarket_buy_levels(polymarket_book)
        if not k or not p:
            raise ValueError("Missing positive displayed depth")
        for n in range(1,101):
            kc,pc=depth_cost(k,n),depth_cost(p,n)
            if not kc["depth_sufficient"] or not pc["depth_sufficient"]:
                break
            total=Decimal(kc["displayed_cost_usd"])+Decimal(pc["displayed_cost_usd"])+n*(fk+fp)
            if total>cap:
                break
            if total>0:
                gain=Decimal(n)-total
                roi=gain/total*100
                if roi>=2:
                    result["scenarios"].append({
                        "contracts_each":n,"displayed_cost_usd":str(total),
                        "hypothetical_net_usd":str(gain),
                        "hypothetical_roi_pct":str(roi.quantize(Decimal("0.001")))})
    except (ValueError,ArithmeticError,TypeError,KeyError) as exc:
        result["reasons"].append(str(exc))
    result["reasons"]+= [
        "Settlement equivalence and event rules not verified",
        "No evidence of executable paired fills or legal trading eligibility",
        "FX, funding, fees beyond inputs, and payout timing unverified"]
    if result["scenarios"]:
        result["largest_displayed_scenario"]=result["scenarios"][-1]
    return result
