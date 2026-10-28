"""Illustrative fee arithmetic for read-only screening; never a verified venue quote.

Rates MUST be checked against the specific market and effective schedule.
"""
from decimal import Decimal, ROUND_CEILING, ROUND_UP

def positive(value):
    x=Decimal(str(value))
    if not x.is_finite() or x<0: raise ValueError("Invalid nonnegative amount")
    return x

def kalshi_general_taker_fee(contracts, price, *, multiplier="1"):
    n,p,m=positive(contracts),positive(price),positive(multiplier)
    if n!=n.to_integral_value() or p>1: raise ValueError("Invalid contracts or price")
    # Standard illustrative 7% curve, rounded upward to whole cents per order.
    return (Decimal("0.07")*m*n*p*(1-p)).quantize(Decimal("0.01"),rounding=ROUND_CEILING)

def polymarket_sports_taker_fee(contracts, price, *, rate=None):
    if rate is None: raise ValueError("Market-specific sports fee rate must be supplied")
    n,p,r=positive(contracts),positive(price),positive(rate)
    if p>1: raise ValueError("Invalid price")
    return (n*r*p*(1-p)).quantize(Decimal("0.00001"),rounding=ROUND_UP)

def cost_screen(*,contracts,kalshi_price,polymarket_price,
                poly_rate=None,kalshi_multiplier=None,extra_cost=None):
    if poly_rate is None or kalshi_multiplier is None or extra_cost is None:
        return {"status":"FEE_INPUTS_REQUIRED","positive_net_verified":False}
    n=positive(contracts);kp=positive(kalshi_price);pp=positive(polymarket_price)
    if n!=n.to_integral_value() or not n or kp>1 or pp>1:
        raise ValueError("Invalid contract quantity or binary price")
    kf=kalshi_general_taker_fee(n,kp,multiplier=kalshi_multiplier)
    pf=polymarket_sports_taker_fee(n,pp,rate=poly_rate)
    total=n*(kp+pp)+kf+pf+positive(extra_cost)
    profit=n-total
    return {"status":"ILLUSTRATIVE_FEES_UNVERIFIED","positive_net_verified":False,
            "contracts_each":int(n),"kalshi_fee_usd":str(kf),
            "polymarket_fee_usd":str(pf),"total_cost_usd":str(total),
            "hypothetical_net_usd":str(profit),
            "paper_budget_pass":total<=100,
            "hypothetical_positive_after_supplied_costs":profit>0 and total<=100,
            "warning":"Not an executable quote. Check specific market rates, fee-on-buy mechanics, settlement, fills and all funding costs."}
