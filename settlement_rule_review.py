"""Manual settlement-rule evidence records; never infer equivalence from labels.

This module produces structured review templates. It does not approve contracts.
"""
import argparse
import json
from pathlib import Path

CHECKS=("event_identity","outcome_definition","overtime","tie_handling",
        "postponement","cancellation","abandonment","forfeit",
        "resolution_source","determination_time","settlement_currency",
        "payout_amount")

def build(mapping):
    if mapping.get("mapping_method")!="exact_event_id_and_two_unambiguous_outcome_labels":
        raise ValueError("Unsupported mapping")
    pairs=mapping.get("opposing_token_map")
    if not isinstance(pairs,dict):
        raise ValueError("Missing opposing outcome mapping")
    records=[]
    for key,token in sorted(pairs.items()):
        if not isinstance(key,str) or "|" not in key or not str(token).strip():
            continue
        ticker,side=key.rsplit("|",1)
        if not ticker or side not in ("YES","NO"):
            continue
        records.append({
            "kalshi_ticker":ticker,"kalshi_side":side,
            "polymarket_token_id":str(token),
            "status":"UNVERIFIED_RULES","rule_equivalence_verified":False,
            "review_required":list(CHECKS),
            "kalshi_rule_source_url":None,"polymarket_rule_source_url":None,
            "kalshi_source_lookup":"Kalshi public market detail: rules_primary and rules_secondary for this ticker",
            "polymarket_source_lookup":"Polymarket Gamma market metadata: description and resolutionSource, resolved by token ID to market ID",
            "source_fields_collected":False,
            "kalshi_rule_text":None,"polymarket_rule_text":None,
            "reviewer":None,"reviewed_at":None,
            "notes":"Matching event identifiers and team labels do not establish equivalent settlement terms."
        })
    return {"research_only":True,"trade_allowed":False,
            "rule_equivalence_verified":False,
            "review_records":records,
            "verified_pairs":0,
            "warning":"All records require independent contract-specific rule evidence and human review; this generator never approves equivalence."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mapping",required=True)
    p.add_argument("--output",default="settlement_rule_review.json")
    a=p.parse_args()
    mapping=json.loads(Path(a.mapping).read_text(encoding="utf-8"))
    result=build(mapping)
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"review_records":len(result["review_records"]),"verified_pairs":0}))
if __name__=="__main__":
    main()
