"""Safe market-title candidate discovery, never a settlement-equivalence assertion.

Accepts two JSON snapshot files. Only emits potential matches for manual review.
No prices, P&L, Telegram notifications or order actions.
"""
import argparse
import json
import re
from pathlib import Path

STOPWORDS={"will","the","a","an","of","in","on","for","at","by","to","be","is","and","or","yes","no"}

def tokens(value):
    return set(re.findall(r"[a-z0-9]+", str(value).lower()))-STOPWORDS

def candidates(a_markets,b_markets,min_similarity=0.55):
    if not (0<=min_similarity<=1):
        raise ValueError("min_similarity must be between 0 and 1")
    out=[]
    for a in a_markets:
        a_title=a.get("title","")
        for b in b_markets:
            b_title=b.get("title","")
            x,y=tokens(a_title),tokens(b_title)
            if not x or not y:
                continue
            score=len(x&y)/len(x|y)
            if score>=min_similarity:
                out.append({
                    "a_contract_id":a.get("ticker") or a.get("contract_id"),
                    "b_contract_id":b.get("ticker") or b.get("contract_id"),
                    "a_title":a_title,"b_title":b_title,
                    "title_similarity":round(score,3),
                    "rule_match_verified":False,
                    "status":"MANUAL_REVIEW_REQUIRED",
                    "warning":"Similar titles do not prove equivalent outcomes, prices, settlement sources or payout timelines."
                })
    return sorted(out,key=lambda r:r["title_similarity"],reverse=True)

def load_markets(path):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload,dict) or not isinstance(payload.get("markets"),list):
        raise ValueError("Expected JSON object containing markets array")
    return payload["markets"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kalshi",required=True,help="Kalshi snapshot JSON")
    p.add_argument("--forecast",required=True,help="Independent, legally obtained ForecastEx snapshot JSON")
    p.add_argument("--threshold",type=float,default=0.55)
    args=p.parse_args()
    matches=candidates(load_markets(args.kalshi),load_markets(args.forecast),args.threshold)
    print(json.dumps({"status":"RESEARCH_ONLY","verified_matches":0,"review_candidates":matches},indent=2))

if __name__=="__main__":
    main()
