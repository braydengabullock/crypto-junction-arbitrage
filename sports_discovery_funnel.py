"""Read-only discovery funnel: quantify where sports matching loses coverage."""
import argparse
import json
from collections import Counter,defaultdict
from pathlib import Path

LEAGUES=("NBA","NFL","NHL","MLB","WNBA")

def league_for(ticker):
    t=str(ticker or "").upper()
    return next((league for league in LEAGUES if t.startswith("KX"+league+"GAME-")),None)

def event_for(ticker):
    t=str(ticker or "")
    return t.rsplit("-",1)[0] if league_for(t) and "-" in t else t

def funnel(kalshi,polymarket,matches,mapping):
    markets=kalshi.get("markets",[])
    pmarkets=polymarket.get("markets",[])
    candidates=matches.get("candidates",[])
    mapped=mapping.get("opposing_token_map",{})
    result={}
    for league in LEAGUES:
        k=[m for m in markets if league_for(m.get("ticker"))==league]
        c=[m for m in candidates if league_for(m.get("kalshi_ticker"))==league
           and m.get("match_method")=="sports_identifier_date_teams_research"]
        discovered={str(m.get("ticker")) for m in k if m.get("ticker")}
        tickers={str(m.get("kalshi_ticker")) for m in c if m.get("kalshi_ticker")} & discovered
        mapped_tickers={key.rsplit("|",1)[0] for key,value in mapped.items() if
                        key.endswith("|YES") and isinstance(value,str) and value.strip()
                        and league_for(key.rsplit("|",1)[0])==league} & tickers
        result[league]={
            "kalshi_contract_sides_discovered":len(k),
            "kalshi_distinct_events_discovered":len({event_for(m.get("ticker")) for m in k}),
            "exact_identifier_matched_sides":len(tickers),
            "exact_identifier_matched_events":len({event_for(t) for t in tickers}),
            "strict_opposing_token_mapped_sides":len(mapped_tickers),
            "strict_opposing_token_mapped_events":len({event_for(t) for t in mapped_tickers}),
            "identifier_matched_but_unmapped_sides":len(tickers-mapped_tickers),
            "identifier_matched_but_unmapped_events":len({event_for(t) for t in tickers-mapped_tickers}),
            "mapping_coverage_pct_of_matched_sides":round(100*len(mapped_tickers)/len(tickers),1) if tickers else None,
            "identifier_match_missing_sides":len(discovered-tickers),
            "identifier_match_missing_events":len({event_for(t) for t in discovered-tickers}),
            "identifier_coverage_pct_of_discovered_sides":round(100*len(tickers)/len(discovered),1) if discovered else None,
            "discovery_bottleneck":("NO_DISCOVERED_CONTRACTS" if not discovered else
                                   "IDENTIFIER_MATCHING" if not tickers else
                                   "TOKEN_MAPPING" if tickers-mapped_tickers else
                                   "DOWNSTREAM_PRICE_AND_RULE_REVIEW")
        }
    return {
        "research_only":True,"verified_opportunities":0,
        "polymarket_markets_sampled":len(pmarkets),
        "polymarket_coverage_complete":polymarket.get("data_quality",{}).get("pagination",{}).get("complete"),
        "matches_candidate_cap_reached":len(candidates)>=int(matches.get("candidate_limit",500)),
        "by_league":result,
        "warning":("Discovery counts are not verified settlement matches or executable opportunities. "
                   +("Candidate matching may be truncated at the configured cap of "
                     +str(matches.get("candidate_limit",500))+". "
                     if len(candidates)>=int(matches.get("candidate_limit",500)) else "")
                   +("Polymarket collection is incomplete; observed mapping coverage may be understated. "
                     if polymarket.get("data_quality",{}).get("pagination",{}).get("complete") is not True else "")
                   +"Strict token mappings are research-only and do not verify settlement equivalence or executable depth.")
    }

def main():
    p=argparse.ArgumentParser()
    for key in ("kalshi","polymarket","matches","mapping"):
        p.add_argument("--"+key,required=True)
    p.add_argument("--output",default="sports_discovery_funnel.json")
    a=p.parse_args()
    result=funnel(*[json.loads(Path(getattr(a,k)).read_text(encoding="utf-8"))
                    for k in ("kalshi","polymarket","matches","mapping")])
    Path(a.output).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"polymarket_markets_sampled":result["polymarket_markets_sampled"],
                      "matches_candidate_cap_reached":result["matches_candidate_cap_reached"],
                      "by_league":result["by_league"]}))
if __name__=="__main__":
    main()
