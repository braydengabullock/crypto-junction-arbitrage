"""Group sports research leads by event identifiers, not by incidental title overlap.

A group is an investigation lead, NEVER a verified same-event pairing.
"""
import json
from collections import defaultdict
from pathlib import Path

def group_leads(shortlist, kalshi_snapshot, polymarket_snapshot):
    by_ticker={str(m.get("ticker")):m for m in kalshi_snapshot.get("markets",[])}
    by_id={str(m.get("id")):m for m in polymarket_snapshot.get("markets",[])}
    groups=defaultdict(lambda:{"kalshi_tickers":set(),"polymarket_ids":set(),"candidate_rows":0})
    skipped=0
    for candidate in shortlist.get("candidates",[]):
        k=by_ticker.get(str(candidate.get("kalshi_ticker")))
        p=by_id.get(str(candidate.get("polymarket_id")))
        if not k or not p or not k.get("event_ticker") or not p.get("slug"):
            skipped+=1
            continue
        # Polymarket slugs are market identities, NOT necessarily event identities.
        key=(str(k["event_ticker"]),str(p["slug"]))
        group=groups[key]
        group["kalshi_tickers"].add(str(k["ticker"]))
        group["polymarket_ids"].add(str(p["id"]))
        group["candidate_rows"]+=1
    leads=[{"kalshi_event_ticker":k,"polymarket_market_slug":p,
            "kalshi_tickers":sorted(v["kalshi_tickers"]),
            "polymarket_ids":sorted(v["polymarket_ids"]),
            "candidate_rows":v["candidate_rows"],
            "event_identity_verified":False,"opposing_outcomes_verified":False,
            "status":"EVENT_IDENTITY_REVIEW_REQUIRED"} for (k,p),v in groups.items()]
    leads.sort(key=lambda x:(-len(x["kalshi_tickers"]),-x["candidate_rows"]))
    for lead in leads:
        lead["review_priority"]="MULTIPLE_KALSHI_OUTCOMES" if len(lead["kalshi_tickers"])>=2 else "SINGLE_CONTRACT_LEAD"
        lead["ready_for_price_validation"]=False
        lead["next_step"]="Verify exact two-team event, matching outcome tokens and resolution conditions before book pricing"
    return {"research_only":True,"event_groups":leads,"groups_found":len(leads),
            "skipped_missing_identifiers":skipped,"verified_pairs":0,
            "warning":"Different exchange identifiers are not proof of matching event, settlement or prices."}

if __name__=="__main__":
    import glob
    def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
    k="kalshi_sports_snapshot.json"
    p=sorted(glob.glob("snapshots/polymarket_*.json"))[-1]
    out=group_leads(load("sports_candidate_shortlist.json"),load(k),load(p))
    Path("sports_event_leads.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"groups_found":out["groups_found"],"skipped":out["skipped_missing_identifiers"],
                      "verified_pairs":0}))
