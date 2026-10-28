"""Conservative research-only opposite-token mapping from exact sports IDs and labels.

Never verifies settlement equivalence; ambiguous names are rejected.
"""
import json
import re
from pathlib import Path
from one_event_outcome_pairs import outcomes

def normalize(value):
    return re.sub(r"[^a-z0-9]+"," ",str(value).casefold()).strip()

def make_mapping(matches):
    grouped={}
    for c in matches:
        if c.get("match_method")!="sports_identifier_date_teams_research":
            continue
        ticker=str(c.get("kalshi_ticker") or "")
        event=ticker.rsplit("-",1)[0]
        if not re.fullmatch(r"KX(?:NBA|NFL|NHL|MLB|WNBA)GAME-\d{2}[A-Z]{3}\d{2}[A-Z]{6}",event):
            continue
        kcode=ticker.rsplit("-",1)[-1]
        if len(kcode)!=3: continue
        key=(event,str(c.get("polymarket_id")),str(c.get("polymarket_slug")))
        grouped.setdefault(key,[]).append(c)
    mapping={}; evidence=[]
    for (event,market_id,slug),cs in grouped.items():
        code_to_row={c["kalshi_ticker"][-3:]:c for c in cs}
        if len(code_to_row)!=2 or len(cs)!=2: continue
        codes=set(code_to_row)
        # Official market outcome labels and token IDs must be retained from
        # snapshot; a title-only match cannot identify the correct token.
        labels=outcomes(cs[0].get("polymarket_outcomes"))
        tokens=outcomes(cs[0].get("polymarket_clob_token_ids"))
        if len(labels)!=2 or len(tokens)!=2 or len(set(map(str,tokens)))!=2: continue
        assignments={}
        for code,row in code_to_row.items():
            title=normalize(row.get("kalshi_title",""))
            subtitle=normalize(row.get("kalshi_subtitle",""))
            options=[]
            for i,label in enumerate(labels):
                name=normalize(label)
                if not name or len(name)<4: continue
                # Require the full outcome label to appear as a word sequence
                # in a Kalshi winner-specific title/subtitle; reject ambiguity.
                if re.search(r"(?<![a-z0-9])"+re.escape(name)+r"(?![a-z0-9])",title+" "+subtitle):
                    options.append(i)
            if len(options)!=1: break
            assignments[code]=options[0]
        if len(assignments)!=2 or len(set(assignments.values()))!=2: continue
        for code,row in code_to_row.items():
            opposing=1-assignments[code]
            token=str(tokens[opposing])
            if not token.isdigit(): break
            mapping[row["kalshi_ticker"]+"|YES"]=token
            evidence.append({"kalshi_ticker":row["kalshi_ticker"],"kalshi_side":"YES",
                "polymarket_market_id":market_id,"opposing_label":labels[opposing],
                "polymarket_token_id":token,"rules_verified":False})
    return {"research_only":True,"mapping_method":"exact_event_id_and_two_unambiguous_outcome_labels",
        "market_rules_verified":False,"opposing_token_map":mapping,"evidence":evidence,
        "mapped_pairs":len(mapping),"warning":"Label-based mappings are candidates only; outcome definitions and settlement rules unverified"}

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--matches",default="research_matches.json")
    a.add_argument("--output",default="opposing_token_map.json")
    z=a.parse_args()
    src=json.loads(Path(z.matches).read_text(encoding="utf-8"))
    out=make_mapping(src.get("candidates",[]))
    Path(z.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"mapped_pairs":out["mapped_pairs"],"rules_verified":False}))
