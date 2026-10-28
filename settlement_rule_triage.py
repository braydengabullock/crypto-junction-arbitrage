"""Conservative text-difference flags for manual settlement-rule review.

Flags are triage hints, not automated determinations of equivalent outcomes.
"""
import argparse
import json
import re
from pathlib import Path

TOPICS={
    "overtime":r"\bovertime\b|\bextra time\b|\bregulation\b",
    "postponement":r"\bpostpon(?:ed|ement|e)\b|\breschedul(?:ed|ing|e)\b",
    "cancellation":r"\bcancell?(?:ed|ation)?\b|\bvoid(?:ed)?\b",
    "forfeit":r"\bforfeit(?:ed|ure)?\b",
    "tie":r"\btie\b|\bdraw\b",
    "abandonment":r"\babandon(?:ed|ment)?\b",
}

def triage(report):
    rows=[]
    for row in report.get("review_records",[]):
        kalshi=" ".join(str(row.get(k) or "") for k in ("kalshi_rule_text","kalshi_rules_secondary"))
        poly=str(row.get("polymarket_rule_text") or "")
        differences=[]
        for topic,pattern in TOPICS.items():
            k=bool(re.search(pattern,kalshi,re.I))
            p=bool(re.search(pattern,poly,re.I))
            if k!=p:
                differences.append({"topic":topic,"kalshi_mentions":k,"polymarket_mentions":p,
                                    "interpretation":"TEXT_MENTION_DIFFERENCE_ONLY"})
        rows.append({"kalshi_ticker":row.get("kalshi_ticker"),
                     "kalshi_side":row.get("kalshi_side"),
                     "polymarket_token_id":row.get("polymarket_token_id"),
                     "rule_texts_collected":bool(row.get("source_fields_collected")),
                     "manual_review_flags":differences,
                     "manual_review_priority":"CHECK_DIFFERENCES" if differences else "READ_BOTH_RULES",
                     "rule_equivalence_verified":False})
    return {"research_only":True,"trade_allowed":False,"verified_pairs":0,
            "records_examined":len(rows),
            "records_with_text_mention_differences":sum(bool(x["manual_review_flags"]) for x in rows),
            "records":rows,
            "warning":"Keyword mention differences are not semantic contradictions. No flags does not mean equivalence; independent manual review required."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="settlement_rule_review.json")
    p.add_argument("--output",default="settlement_rule_triage.json")
    a=p.parse_args()
    result=triage(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"records_examined":result["records_examined"],
                      "records_with_text_mention_differences":result["records_with_text_mention_differences"],
                      "verified_pairs":0}))
if __name__=="__main__":
    main()
