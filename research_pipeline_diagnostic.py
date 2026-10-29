"""Explain where read-only cross-venue research candidates drop out."""
import argparse
import json
from collections import Counter
from pathlib import Path

def diagnose(books, pricing, capital, efficiency):
    rows=books.get("rows",[])
    priced=pricing.get("near_misses",[])
    positive=pricing.get("rows",[])
    reasons=Counter()
    for row in rows:
        obs=row.get("observations",[])
        venues={x.get("venue") for x in obs if isinstance(x,dict)}
        if not {"kalshi","polymarket"}.issubset(venues):
            reasons["MISSING_ONE_OR_BOTH_BOOKS"]+=1
        elif row.get("errors"):
            reasons["BOOKS_PRESENT_WITH_FETCH_WARNINGS"]+=1
        else:
            reasons["BOOKS_PRESENT_NO_RECORDED_FETCH_ERRORS"]+=1
    data={
        "research_only":True,"trade_allowed":False,"verified_opportunities":0,
        "rows_sampled":len(rows),"book_collection_categories":dict(reasons),
        "opposing_mapping_screen_status":pricing.get("status","UNKNOWN"),
        "mapped_pairs_with_modeled_costs":len(priced),
        "positive_modeled_profit_candidates":len(positive),
        "nonpositive_priced_pairs":sum(1 for x in priced if x.get("scenario",{}).get("net_roi_tier")=="NONPOSITIVE_REJECT"),
        "capital_audit_status":capital.get("evidence_status","UNKNOWN"),
        "capital_audit_checked":capital.get("scenarios_checked",0),
        "capital_audit_issues":capital.get("issues",[]),
        "efficiency_scenarios_compared":efficiency.get("matched_scenarios_compared",0),
        "unverified_cost_input_caveat":pricing.get("fx_cost_supplied") is not True,
        "warning":"Counts are observations, not verified executable trades. Sampling, mappings, rules, FX, and execution quality remain unverified."
    }
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--books",default="candidate_orderbooks.json")
    p.add_argument("--pricing",default="depth_fee_illustrative.json")
    p.add_argument("--capital",default="capital_audit.json")
    p.add_argument("--efficiency",default="capital_efficiency.json")
    p.add_argument("--output",default="research_pipeline_diagnostic.json")
    a=p.parse_args()
    sources=[json.loads(Path(x).read_text(encoding="utf-8")) for x in (a.books,a.pricing,a.capital,a.efficiency)]
    out=diagnose(*sources)
    Path(a.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out))
if __name__=="__main__":
    main()
