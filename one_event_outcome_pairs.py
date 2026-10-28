"""Research-only outcome mapping with explicit event and team identities.

Candidates are NOT verified complementary payouts or executable opportunities.
"""
import json

def outcomes(value):
    if isinstance(value,str):
        try: value=json.loads(value)
        except ValueError: return []
    return value if isinstance(value,list) else []

def pair_game_winners_for_event(kalshi_event,polymarket_event, *,
                                kalshi_event_ticker,polymarket_question,teams):
    """Map one explicit two-team event; never infer pair identity from title overlap.

    teams: {"OKC": {"kalshi_title": "Oklahoma City",
                    "polymarket_labels": ["Thunder","Oklahoma City"]}, ...}
    """
    if len(teams)!=2 or len(set(teams))!=2: raise ValueError("Two distinct teams required")
    pairs=[]
    k=kalshi_event.get("markets",[])
    p=polymarket_event.get("markets",[])
    for pm in p:
        if pm.get("question")!=polymarket_question: continue
        labels=outcomes(pm.get("outcomes"))
        tokens=outcomes(pm.get("clobTokenIds"))
        if len(labels)!=2 or len(tokens)!=2 or len(set(map(str,tokens)))!=2: continue
        for label,token in zip(labels,tokens):
            for code, team in teams.items():
                allowed={str(x).casefold().strip() for x in team["polymarket_labels"]}
                if str(label).casefold().strip() not in allowed: continue
                ticker=kalshi_event_ticker+"-"+code
                for km in k:
                    if km.get("ticker")!=ticker: continue
                    title=str(km.get("title","")).casefold()
                    if team["kalshi_title"].casefold() not in title: continue
                    pairs.append({"kalshi_ticker":ticker,"kalshi_side":"YES",
                        "team":code,"polymarket_token_id":str(token),
                        "polymarket_outcome":label,"polymarket_market_id":pm.get("id"),
                        "market_rules_verified":False,"price_verified":False,
                        "status":"OUTCOME_LABEL_CANDIDATE_ONLY"})
    # A candidate event is valid only if exactly two distinct outcomes are mapped.
    if len(pairs)!=2 or {x["team"] for x in pairs}!=set(teams): return []
    return pairs

def pair_game_winners(kalshi_event,polymarket_event):
    return pair_game_winners_for_event(
        kalshi_event,polymarket_event,
        kalshi_event_ticker="KXNBAGAME-26OCT28OKCDAL",
        polymarket_question="Thunder vs. Mavericks",
        teams={"OKC":{"kalshi_title":"Oklahoma City",
                      "polymarket_labels":["Thunder","Oklahoma City"]},
               "DAL":{"kalshi_title":"Dallas",
                      "polymarket_labels":["Mavericks","Dallas"]}})
