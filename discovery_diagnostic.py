"""Research diagnostics for why two sampled venue inventories do not match."""
import argparse
import json
from collections import Counter
from pathlib import Path
from market_comparison import candidate_words, SPORT_TERMS, candidate_score

def diagnose(kalshi, polymarket, *, sample_size=8):
    left=kalshi["markets"]; right=polymarket["markets"]
    a=[candidate_words(x,kalshi=True) for x in left]
    b=[candidate_words(x) for x in right]
    sports_a=sum(bool(words & SPORT_TERMS) for words in a)
    sports_b=sum(bool(words & SPORT_TERMS) for words in b)
    # Diagnostic candidates, NOT market matches: ignore shared single terms.
    index={}
    for i, words in enumerate(b):
        for word in words:
            if len(word)>3:
                index.setdefault(word,set()).add(i)
    near=[]
    for i,words in enumerate(a):
        possible=set()
        for word in words:
            if len(word)>3:
                possible.update(index.get(word,()))
        ranked=[]
        for j in possible:
            common=words & b[j]
            if len(common)<2: continue
            score=candidate_score(words,b[j])
            if score<0.25: continue
            ranked.append((score,j))
        if ranked:
            score,j=max(ranked)
            near.append({"kalshi_ticker":left[i].get("ticker"),
                         "kalshi_title":left[i].get("title"),
                         "polymarket_id":right[j].get("id"),
                         "polymarket_question":right[j].get("question"),
                         "lexical_score":round(score,3),
                         "rule_equivalence_verified":False})
    near.sort(key=lambda x:x["lexical_score"],reverse=True)
    return {"research_only":True,"diagnostic_only":True,
            "kalshi_markets":len(left),"polymarket_markets":len(right),
            "sports_keyword_markets":{"kalshi":sports_a,"polymarket":sports_b},
            "kalshi_coverage_complete":kalshi.get("data_quality",{}).get("pagination",{}).get("complete"),
            "polymarket_coverage_complete":polymarket.get("data_quality",{}).get("pagination",{}).get("complete"),
            "near_match_examples_unverified":near[:sample_size],
            "near_match_candidate_count":len(near),
            "warning":"Token overlap is not event identity. These are diagnostic examples, not executable or verified contracts."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kalshi",required=True)
    p.add_argument("--polymarket",required=True)
    p.add_argument("--output",default="discovery_diagnostic.json")
    a=p.parse_args()
    k=json.loads(Path(a.kalshi).read_text(encoding="utf-8"))
    m=json.loads(Path(a.polymarket).read_text(encoding="utf-8"))
    if k.get("source")!="kalshi_public" or m.get("source")!="polymarket_gamma_public":
        raise ValueError("Expected public research snapshots")
    result=diagnose(k,m)
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({key:val for key,val in result.items() if key!="near_match_examples_unverified"}))
if __name__=="__main__":
    main()
