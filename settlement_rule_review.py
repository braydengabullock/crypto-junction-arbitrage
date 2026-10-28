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

def tokens(value):
    if isinstance(value,str):
        try:
            value=json.loads(value)
        except (ValueError,TypeError):
            return []
    return [str(x) for x in value] if isinstance(value,list) else []

def enrich(report,kalshi,polymarket):
    """Attach source fields from saved public snapshots; no equivalence inference."""
    ks={str(m.get("ticker")):m for m in kalshi.get("markets",[]) if m.get("ticker")}
    ps={}
    for m in polymarket.get("markets",[]):
        for token in tokens(m.get("clobTokenIds")):
            ps[token]=m
    for row in report["review_records"]:
        k=ks.get(row["kalshi_ticker"],{})
        p=ps.get(row["polymarket_token_id"],{})
        ticker=row["kalshi_ticker"]
        row["kalshi_rule_source_url"]="https://kalshi.com/markets/"+ticker if k else None
        row["polymarket_rule_source_url"]=("https://polymarket.com/event/"+str(p["slug"])) if p.get("slug") else None
        row["kalshi_rule_text"]=k.get("rules_primary") or None
        row["kalshi_rules_secondary"]=k.get("rules_secondary") or None
        row["polymarket_rule_text"]=p.get("description") or None
        row["polymarket_resolution_source"]=p.get("resolutionSource") or None
        row["polymarket_market_id"]=str(p["id"]) if p.get("id") is not None else None
        row["source_fields_collected"]=bool(row["kalshi_rule_text"] and row["polymarket_rule_text"])
        row["status"]="RULE_TEXT_COLLECTED_REVIEW_REQUIRED" if row["source_fields_collected"] else "RULE_EVIDENCE_INCOMPLETE"
        row["rule_equivalence_verified"]=False
    report["records_with_both_rule_texts"]=sum(x["source_fields_collected"] for x in report["review_records"])
    return report

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
    p.add_argument("--kalshi",help="Saved public Kalshi snapshot")
    p.add_argument("--polymarket",help="Saved public Polymarket snapshot")
    a=p.parse_args()
    if bool(a.kalshi)!=bool(a.polymarket):
        p.error("Both venue snapshots are required together")
    mapping=json.loads(Path(a.mapping).read_text(encoding="utf-8"))
    result=build(mapping)
    if a.kalshi:
        result=enrich(result,json.loads(Path(a.kalshi).read_text(encoding="utf-8")),
                      json.loads(Path(a.polymarket).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"review_records":len(result["review_records"]),"verified_pairs":0,"records_with_both_rule_texts":result.get("records_with_both_rule_texts",0)}))
if __name__=="__main__":
    main()
