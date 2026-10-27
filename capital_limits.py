"""Pure capital-allocation checks. No account connections or transfers."""
from decimal import Decimal, InvalidOperation

def dec(value):
    x=Decimal(str(value))
    if not x.is_finite() or x < 0:
        raise ValueError("Balance and allocation must be nonnegative finite numbers")
    return x

def capital_check(pair_result, *, balance_a, balance_b, portfolio_total,
                  total_current_committed, per_venue_reserve_pct=30,
                  max_exposure_pct=25):
    """Evaluate supplied balances; never claim independently verified balances."""
    try:
        available_a=dec(balance_a)
        available_b=dec(balance_b)
        portfolio=dec(portfolio_total)
        committed=dec(total_current_committed)
        allocation_a=dec(pair_result["allocation_a_usd"])
        allocation_b=dec(pair_result["allocation_b_usd"])
        reserve=dec(per_venue_reserve_pct)/100
        cap=dec(max_exposure_pct)/100
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        return {"allowed":False,"reasons":["Invalid balance inputs: "+str(exc)]}
    problems=[]
    if portfolio <= 0:
        problems.append("Portfolio balance must be positive")
    if not Decimal("0") <= reserve < Decimal("1"):
        problems.append("Invalid reserve percentage")
    if not Decimal("0") < cap <= Decimal("1"):
        problems.append("Invalid maximum exposure percentage")
    # Balance fields are actual *available* cash and the reserves are held out
    # from those balances. Calculations fail closed on missing/invalid inputs.
    if allocation_a > available_a * (1-reserve):
        problems.append("Venue A reserve or available balance would be breached")
    if allocation_b > available_b * (1-reserve):
        problems.append("Venue B reserve or available balance would be breached")
    if committed + allocation_a + allocation_b > portfolio * cap:
        problems.append("Portfolio concurrent exposure cap would be breached")
    return {"allowed":not problems,"reasons":problems}
