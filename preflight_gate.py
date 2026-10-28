"""Preflight gate: observation test readiness, never trading readiness."""
import argparse
import json
from pathlib import Path

def assess(matches, books, quality, report):
    issues=[]
    if matches.get("research_only") is not True or books.get("research_only") is not True:
        issues.append("Research-only source labels missing")
    if quality.get("research_only") is not True or report.get("research_only") is not True:
        issues.append("Research-only quality labels missing")
    n=quality.get("rows_examined")
    if not isinstance(n,int) or n<0:
        issues.append("No valid sampled candidate count")
    if not isinstance(books.get("rows"),list) or len(books["rows"])!=n:
        issues.append("Orderbook rows inconsistent with quality report")
    if matches.get("candidates_returned") != books.get("candidate_count") and matches.get("candidates_returned") is not None:
        issues.append("Candidate count mismatch")
    if report.get("verified_trade_opportunities")!=0 or report.get("actual_profit_usd") is not None:
        issues.append("Invalid claim of verified profit")
    for row in books.get("rows",[]):
        if row.get("executable_opportunity_verified") is not False:
            issues.append("Unexpected executable-opportunity claim")
    # No candidates is a valid observed result, not proof of a functioning pairing engine.
    if n==0:
        issues.append("No candidate orderbooks sampled; no usable paired-market evidence")
    if quality.get("rows_with_synchronized_observations",0)==0:
        issues.append("No synchronized cross-exchange books")
    if quality.get("rows_with_displayed_depth_on_both_venues",0)==0:
        issues.append("No displayed depth on both venues")
    details=quality.get("details",[])
    if not isinstance(details,list) or len(details)!=n:
        issues.append("Missing per-candidate quality evidence")
    elif not any(item.get("both_books") and item.get("synchronized")
                 and item.get("displayed_depth_on_both") and not item.get("issues")
                 for item in details if isinstance(item,dict)):
        issues.append("No single candidate has synchronized, usable books on both venues")
    return {"gate":"OBSERVATION_DIAGNOSTIC","data_sufficient_for_paper_backtest":False,
            "observation_usable":not issues,
            "issues":issues,
            "verified_trades":0,
            "warning":"Even an observation-usable result is NOT an actionable arbitrage or profitability backtest."}

def main():
    p=argparse.ArgumentParser()
    for field in ("matches","books","quality","report"):
        p.add_argument("--"+field,required=True)
    p.add_argument("--output",default="preflight_report.json")
    a=p.parse_args()
    result=assess(*[json.loads(Path(getattr(a,k)).read_text(encoding="utf-8"))
                    for k in ("matches","books","quality","report")])
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
