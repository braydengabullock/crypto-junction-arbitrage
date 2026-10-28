"""Rank sports-like title candidates for MANUAL outcome/rules review only.

No event identity, price, or arb claim is inferred from text similarity.
"""
import json
from pathlib import Path
from market_comparison import eligible_for_simple_match

def shortlist(matches, *, limit=25):
    if limit<1: raise ValueError("Positive cap required")
    candidates=matches.get("candidates",[])
    result=[]
    seen=set()
    for m in sorted(candidates,key=lambda x:x.get("title_similarity",0),reverse=True):
        if not m.get("sports_candidate"): continue
        if not eligible_for_simple_match({"ticker":m.get("kalshi_ticker"),"title":m.get("kalshi_title")},kalshi=True): continue
        if not eligible_for_simple_match({"question":m.get("polymarket_question")}): continue
        # sports_candidate already came from the upstream classifier. Requiring
        # a sport name AGAIN loses team-only markets (e.g. Thunder vs Mavericks).
        key=(str(m.get("kalshi_ticker")),str(m.get("polymarket_id")))
        if key in seen: continue
        seen.add(key)
        result.append({
          "kalshi_ticker":key[0],"polymarket_id":key[1],
          "kalshi_title":m.get("kalshi_title"),
          "polymarket_question":m.get("polymarket_question"),
          "similarity":m.get("title_similarity"),
          "polymarket_token_ids":m.get("polymarket_clob_token_ids"),
          "rules_verified":False,"opposing_outcomes_verified":False,
          "executable_prices_verified":False,"net_roi_verified":False,
          "status":"TITLE_CANDIDATE_ONLY",
          "next_review":"Check Kalshi event ticker and Polymarket event slug, team identities, date and winner market type before quote requests"})
        if len(result)>=limit: break
    return {"research_only":True,"source":"sports_title_candidate_shortlist",
            "sports_candidates_returned":len(result),
            "candidates":result,"verified_paired_opportunities":0,
            "note":"Sports-looking titles are lead generation only. Explicit same-game and opposing-outcome mapping plus rules and depth required."}

if __name__=="__main__":
    data=json.loads(Path("research_matches.json").read_text(encoding="utf-8"))
    output=shortlist(data)
    Path("sports_candidate_shortlist.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
    print(json.dumps({"sports_candidates":len(output["candidates"]),
                      "verified_opportunities":0}))
