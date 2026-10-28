"""Research-only Kalshi ↔ Polymarket title comparison.

Potentially similar titles are NEVER proof of equivalent resolution.
No execution, Telegram, modeled arbitrage profit or automatic trading.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STOP = {"will","the","a","an","at","on","of","in","to","by","before","after",
        "for","be","is","and","or","yes","no","does","that","this","market",
        "price","above","below","vs","versus","against","beat","defeat",
        "wins","win","winner","game","match","team","teams"}
TOKEN = re.compile(r"[a-z0-9]+")
ALIASES = {"ny":"new york","la":"los angeles","sf":"san francisco",
           "nyc":"new york city","utd":"united"}
SPORT_TERMS = {"nba","nfl","nhl","mlb","wnba","soccer","football","basketball","hockey","baseball","tennis","match","game","win","winner","beat","defeat"}

SPORT_TICKER_PREFIXES = ("KXNBAGAME", "KXNFLGAME", "KXNHLGAME", "KXMLBGAME", "KXWNBAGAME")
SPORT_SLUG_PREFIXES = ("nba-", "nfl-", "nhl-", "mlb-", "wnba-")

def is_sports_candidate(kalshi_market, poly_market, words):
    ticker=str(kalshi_market.get("ticker") or "").upper()
    slug=str(poly_market.get("slug") or "").lower()
    return bool((words & SPORT_TERMS) or
                (ticker.startswith(SPORT_TICKER_PREFIXES) and
                 slug.startswith(SPORT_SLUG_PREFIXES)))


SPORT_CODES={"NBA":"nba","NFL":"nfl","NHL":"nhl","MLB":"mlb","WNBA":"wnba"}
MONTHS={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}

def sports_identifier_match(kalshi_market, poly_market):
    """Conservative date/league/team-code match, not payout or rule equivalence."""
    ticker=str(kalshi_market.get("ticker") or "").upper()
    slug=str(poly_market.get("slug") or "").lower()
    m=re.fullmatch(r"KX(NBA|NFL|NHL|MLB|WNBA)GAME-(\\d{2})([A-Z]{3})(\\d{2})([A-Z]{6})-([A-Z]{3})",ticker)
    if not m: return False
    league,yy,mon,day,teams,winner=m.groups()
    if mon not in MONTHS: return False
    a,b=teams[:3],teams[3:]
    if a==b or winner not in (a,b): return False
    try:
        from datetime import date
        actual=date(2000+int(yy),MONTHS[mon],int(day)).isoformat()
    except ValueError: return False
    expected=f"{SPORT_CODES[league]}-{a.lower()}-{b.lower()}-{actual}"
    reverse=f"{SPORT_CODES[league]}-{b.lower()}-{a.lower()}-{actual}"
    return slug in (expected,reverse)

def candidate_words(market, *, kalshi=False):
    """Use descriptive event fields; never use rule text to create a match."""
    primary = market.get("title") if kalshi else market.get("question")
    supplementary = market.get("subtitle") if kalshi else None
    return tokenize(" ".join(str(v) for v in (primary,supplementary) if v))

def eligible_for_simple_match(market, *, kalshi=False):
    """Reject bundles/parlays from simple two-outcome matching.
    
    A cross-category contract cannot be paired with one ordinary event.
    Remaining records still require formal rule and outcome verification.
    """
    title=str(market.get("title") or market.get("question") or "")
    ticker=str(market.get("ticker") or "")
    if kalshi and ("CROSSCATEGORY" in ticker.upper() or "PARLAY" in ticker.upper()):
        return False
    if len(title)>240 or len(tokenize(title))>35 or title.count(",")>=5:
        return False
    return True

def candidate_score(left, right):
    # Overlap coefficient helps discover alternate wordings, but remains unverified.
    if not left or not right: return 0.0
    intersect=len(left & right)
    jaccard=intersect/len(left | right)
    containment=intersect/min(len(left),len(right))
    return max(jaccard,containment*0.80) if intersect >= 2 else jaccard

def tokenize(text):
    raw = str(text).lower()
    raw = re.sub(r"\\b(" + "|".join(re.escape(k) for k in ALIASES) + r")\\b",
                 lambda match: ALIASES[match.group(0)], raw)
    return set(TOKEN.findall(raw)) - STOP

def compare(kalshi, polymarket, *, threshold=0.55, max_results=100):
    if not 0 <= threshold <= 1 or max_results < 1:
        raise ValueError("Invalid matching threshold or result cap")
    index=defaultdict(list)
    p_markets=polymarket["markets"]
    for ix, market in enumerate(p_markets):
        if not eligible_for_simple_match(market): continue
        if market.get("enableOrderBook") is False or market.get("acceptingOrders") is False: continue
        for word in candidate_words(market):
            index[word].append(ix)
    results=[]
    for market in kalshi["markets"]:
        if not eligible_for_simple_match(market,kalshi=True): continue
        title=market.get("title") or ""
        words=candidate_words(market,kalshi=True)
        if not words:
            continue
        ids=set()
        for word in words:
            ids.update(index[word])
        for ix,other in enumerate(p_markets):
            if eligible_for_simple_match(other) and other.get("enableOrderBook") is not False and other.get("acceptingOrders") is not False and sports_identifier_match(market,other):
                ids.add(ix)
        for ix in ids:
            other=p_markets[ix]
            other_words=candidate_words(other)
            score=candidate_score(words,other_words)
            ident_match=sports_identifier_match(market,other)
            if score >= threshold or ident_match:
                results.append({
                    "kalshi_ticker":market.get("ticker"),
                    "polymarket_id":other.get("id"),
                    "polymarket_slug":other.get("slug"),
                    "kalshi_title":title,
                    "polymarket_question":other.get("question"),
                    "kalshi_rules_excerpt":market.get("rules_primary"),
                    "polymarket_description":other.get("description"),
                    "polymarket_resolution_source":other.get("resolutionSource"),
                    "kalshi_expiration_time":market.get("expiration_time"),
                    "polymarket_end_date":other.get("endDate"),
                    "polymarket_clob_token_ids":other.get("clobTokenIds"),
                    "polymarket_orderbook_enabled":other.get("enableOrderBook"),
                    "polymarket_accepting_orders":other.get("acceptingOrders"),
                    "kalshi_rule_url":None,
                    "polymarket_rule_url":None,
                    "review_required":[
                        "Locate both official complete rule texts and official links",
                        "Verify identical event definitions, source, window, exclusions and dispute handling",
                        "Confirm exact opposing YES/NO token identifiers and $1 payout convention",
                        "Verify two-venue trading eligibility and funding/settlement timing",
                        "Obtain synchronized executable orderbook depth and all fees"
                    ],
                    "title_similarity":round(score,3),
                    "match_method":"sports_identifier_date_teams_research" if ident_match else "title_subtitle_token_containment_research",
                    "sports_candidate":ident_match or is_sports_candidate(market,other,words | other_words),
                    "shared_event_terms":sorted(words & other_words),
                    "kalshi_subtitle":market.get("subtitle"),
                    "market_rules_verified":False,
                    "price_comparison_verified":False,
                    "tradable":False,
                    "status":"MANUAL_REVIEW_ONLY"
                })
    results.sort(key=lambda item:item["title_similarity"],reverse=True)
    return results[:max_results],len(results)

def read_snapshot(path, expected):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or obj.get("source")!=expected or obj.get("research_only") is not True or not isinstance(obj.get("markets"),list):
        raise ValueError("Invalid or non-research snapshot: "+expected)
    return obj

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--kalshi",required=True)
    parser.add_argument("--polymarket",required=True)
    parser.add_argument("--output",default="research_matches.json")
    parser.add_argument("--threshold",type=float,default=0.55)
    args=parser.parse_args()
    k=read_snapshot(args.kalshi,"kalshi_public")
    p=read_snapshot(args.polymarket,"polymarket_gamma_public")
    matches,count=compare(k,p,threshold=args.threshold)
    result={
        "source":"kalshi_polymarket_title_research",
        "created_at":datetime.now(timezone.utc).isoformat(),
        "research_only":True,
        "verified_matches":0,
        "potential_title_matches_found":count,
        "candidates_returned":len(matches),
        "snapshot_times":{"kalshi":k.get("observed_at"),"polymarket":p.get("observed_at")},
        "coverage_note":"Both source feeds are paginated samples; timing may differ.",
        "warning":"Title overlap DOES NOT imply equivalent rules, payout, executable prices, legal eligibility, or arbitrage. Do not trade.",
        "candidates":matches,
    }
    Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"research_only":True,"candidates":len(matches),"verified_matches":0,"output":args.output}))

if __name__=="__main__":
    main()
