"""Conservative offline evidence audit for historical paired contract observations.

Does not discover markets, simulate imaginary fills, or assert live profitability.
Requires explicitly supplied, independently verified source evidence. Each row
must represent a real timestamped historical observation and its ultimate payout.
No trading, Telegram messaging, keys or network access.
"""
import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path

MONEY=Decimal("0.01")
def dec(value):
    v=Decimal(str(value))
    if not v.is_finite() or v < 0:
        raise ValueError("Invalid nonnegative numeric input")
    return v

def evaluate(row, *, budget="100", roi_floor="2"):
    required=("id","source_a","source_b","side_a","side_b",
              "ask_a","ask_b","depth_a","depth_b","fee_a_per_contract",
              "fee_b_per_contract","verified_rule_equivalence",
              "verified_execution_quotes","verified_trading_eligibility",
              "verified_settlement","actual_payout_per_pair",
              "observed_quote_time_a","observed_quote_time_b",
              "actual_settlement_time")
    missing=[x for x in required if x not in row or row[x] is None]
    if missing:
        return {"id":row.get("id"),"status":"INSUFFICIENT_EVIDENCE",
                "reasons":["Missing: "+", ".join(missing)]}
    reasons=[]
    if row["source_a"]==row["source_b"]:
        reasons.append("Same underlying exchange")
    if (str(row["side_a"]).upper(),str(row["side_b"]).upper()) not in (("YES","NO"),("NO","YES")):
        reasons.append("Not complementary YES/NO")
    for flag in ("verified_rule_equivalence","verified_execution_quotes",
                 "verified_trading_eligibility","verified_settlement"):
        if row[flag] is not True:
            reasons.append("Unverified: "+flag)
    try:
        from datetime import datetime, timezone
        def stamp(val):
            t=datetime.fromisoformat(str(val).replace("Z","+00:00"))
            if t.tzinfo is None:
                raise ValueError("Timestamps require timezone")
            return t.astimezone(timezone.utc)
        ta,tb,settled=map(stamp,(row["observed_quote_time_a"],
                                  row["observed_quote_time_b"],row["actual_settlement_time"]))
        if abs((ta-tb).total_seconds())>20:
            reasons.append("Non-synchronized quotes")
        if settled < max(ta,tb):
            reasons.append("Settlement before observed quotes")
        a,b=dec(row["ask_a"]),dec(row["ask_b"])
        fa,fb=dec(row["fee_a_per_contract"]),dec(row["fee_b_per_contract"])
        depth_a,depth_b=dec(row["depth_a"]),dec(row["depth_b"])
        payout=dec(row["actual_payout_per_pair"])
        if a>1 or b>1 or depth_a!=depth_a.to_integral_value() or depth_b!=depth_b.to_integral_value():
            reasons.append("Invalid contract ask or depth")
        per_pair=a+b+fa+fb
        qty=min(int(depth_a),int(depth_b),
                int((dec(budget)/per_pair).to_integral_value(rounding=ROUND_FLOOR))) if per_pair>0 else 0
        if qty<=0:
            reasons.append("No paired fill depth within budget")
        spent=per_pair*qty
        gain=(payout-per_pair)*qty
        roi=(gain/spent*100) if spent else Decimal(0)
        projected_roi=((Decimal(1)-per_pair)/per_pair*100) if per_pair else Decimal(0)
        if projected_roi < dec(roi_floor):
            reasons.append("Below required modeled net ROI")
    except (TypeError,ValueError,InvalidOperation,OverflowError) as exc:
        return {"id":row.get("id"),"status":"INSUFFICIENT_EVIDENCE","reasons":[str(exc)]}
    if reasons:
        return {"id":row["id"],"status":"NOT_VALIDATED","reasons":reasons}
    # User-provided boolean evidence still cannot prove historical fills.
    return {"id":row["id"],"status":"CONDITIONAL_PAPER_RESULT",
            "contracts_per_leg":qty,
            "modeled_cost_usd":str(spent.quantize(MONEY)),
            "modeled_profit_usd":str(gain.quantize(MONEY)),
            "modeled_net_roi_pct":str(roi.quantize(Decimal("0.001"))),
            "entry_projected_roi_pct":str(projected_roi.quantize(Decimal("0.001"))),
            "caveat":"Evidence flags and payouts supplied externally; no authenticated historical fills verified."}

def audit(rows):
    if not isinstance(rows,list):
        raise ValueError("Expected list of historical observations")
    results=[evaluate(row) for row in rows]
    valid=[r for r in results if r["status"]=="CONDITIONAL_PAPER_RESULT"]
    profit=sum((Decimal(x["modeled_profit_usd"]) for x in valid),Decimal(0))
    wins=sum(1 for x in valid if Decimal(x["modeled_profit_usd"])>0)
    losses=sum(1 for x in valid if Decimal(x["modeled_profit_usd"])<0)
    return {"type":"HISTORICAL_RESEARCH_AUDIT","actual_realized_profit_usd":None,
            "observations":len(results),"conditional_paper_observations":len(valid),
            "unverified_or_rejected":len(results)-len(valid),
            "conditional_modeled_profit_usd":str(profit.quantize(MONEY)),
            "conditional_wins":wins,"conditional_losses":losses,
            "warning":"Not an estimate of realized or achievable profit. Selection bias, unfilled orders, slippage, FX and unverified payout timelines can invalidate results.",
            "results":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="local_backtest_audit.json")
    args=p.parse_args()
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=audit(data)
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"observations":result["observations"],
                      "conditional_paper_observations":result["conditional_paper_observations"],
                      "actual_realized_profit_usd":None,
                      "output":args.output}))
if __name__=="__main__":
    main()
