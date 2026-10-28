"""Read-only explicit game outcome pairing from event metadata.

Mapping is only a hypothesis. Resolution rule identity is NEVER assumed.
"""
import json

def outcomes(value):
    if isinstance(value,str):
        try: value=json.loads(value)
        except ValueError: return []
    return value if isinstance(value,list) else []

def pair_game_winners(kalshi_event,polymarket_event):
    k=kalshi_event.get("markets",[])
    p=polymarket_event.get("markets",[])
    pairs=[]
    for pm in p:
        if pm.get("question")!="Thunder vs. Mavericks": continue
        labels=outcomes(pm.get("outcomes"))
        tokens=outcomes(pm.get("clobTokenIds"))
        if len(labels)!=2 or len(tokens)!=2: continue
        for label, token in zip(labels,tokens):
            name=str(label).lower().strip()
            if "thunder" in name or name in ("okc","oklahoma city"):
                expected="okc"
            elif "mavericks" in name or name in ("dal","dallas"):
                expected="dal"
            else: continue
            for km in k:
                ticker=str(km.get("ticker","")).lower()
                title=str(km.get("title","")).lower()
                if not ticker.startswith("kxnbagame-26oct28okcdal-"): continue
                suffix=ticker.rsplit("-",1)[-1]
                if suffix != expected: continue
                if expected=="okc" and not ("oklahoma" in title or "thunder" in title): continue
                if expected=="dal" and not ("dallas" in title or "mavericks" in title): continue
                pairs.append({"event":"2026-10-28 OKC vs DAL",
                    "team":expected.upper(),"kalshi_ticker":km["ticker"],
                    "kalshi_side":"YES","polymarket_token_id":str(token),
                    "polymarket_outcome":label,
                    "polymarket_market_id":pm.get("id"),
                    "market_rules_verified":False,"price_verified":False,
                    "status":"OUTCOME_LABEL_CANDIDATE_ONLY"})
    return pairs
