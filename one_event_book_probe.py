"""Inspect focused event evidence, probe public books, never infer rule equivalence."""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from orderbook_research import fetch_kalshi_book, fetch_polymarket_book
from candidate_orderbooks import parse_tokens
from orderbook_research import kalshi_buy_levels, polymarket_buy_levels

def inspect(evidence, *, fetch_k=fetch_kalshi_book, fetch_p=fetch_polymarket_book):
    sources=evidence.get("sources",{})
    k=sources.get("kalshi_event",{}).get("data",{})
    p=sources.get("polymarket_event",{}).get("data",{})
    kalshi=k.get("markets",[]) if isinstance(k,dict) else []
    poly=p.get("markets",[]) if isinstance(p,dict) else []
    if not isinstance(kalshi,list): kalshi=[]
    if not isinstance(poly,list): poly=[]
    report={"research_only":True,"event":evidence.get("event"),
            "captured_at":datetime.now(timezone.utc).isoformat(),
            "event_api_errors":evidence.get("errors",[]),
            "both_event_apis_returned":bool(k and p),
            "status":"NEEDS_MANUAL_RULE_AND_OUTCOME_REVIEW",
            "rule_equivalence_verified":False,"tradable":False,
            "kalshi_contracts":[],"polymarket_contracts":[],
            "book_probes":[],"errors":[]}
    for market in kalshi[:6]:
        ticker=market.get("ticker")
        report["kalshi_contracts"].append({
            "ticker":ticker,"title":market.get("title"),
            "subtitle":market.get("subtitle"),
            "rules_primary":market.get("rules_primary"),
            "status":market.get("status")})
        if ticker:
            try:
                book=fetch_k(ticker)
                fp=book.get("orderbook_fp",{})
                report["book_probes"].append({"venue":"kalshi","ticker":ticker,
                   "book_returned":True,
                   "yes_bid_levels":len(fp.get("yes_dollars",[])),
                   "no_bid_levels":len(fp.get("no_dollars",[])),
                   "yes_buy_best_ask":str(kalshi_buy_levels(book,"YES")[0][0]) if kalshi_buy_levels(book,"YES") else None,
                   "no_buy_best_ask":str(kalshi_buy_levels(book,"NO")[0][0]) if kalshi_buy_levels(book,"NO") else None})
            except (ValueError,HTTPError,URLError,TimeoutError) as e:
                report["errors"].append({"venue":"kalshi","ticker":ticker,
                    "kind":type(e).__name__,"http_status":getattr(e,"code",None)})
    # Only compare the actual game-winner market; props such as first score are not complements.
    for market in [m for m in poly if m.get("question") == "Thunder vs. Mavericks"][:1]:
        tokens=parse_tokens(market.get("clobTokenIds"))
        report["polymarket_contracts"].append({
            "id":market.get("id"),"question":market.get("question"),
            "outcomes":market.get("outcomes"),"clobTokenIds":tokens,
            "enableOrderBook":market.get("enableOrderBook"),
            "acceptingOrders":market.get("acceptingOrders"),
            "description":market.get("description"),
            "indicative_outcome_prices":market.get("outcomePrices"),
            "indicative_only_not_executable":True})
        if market.get("enableOrderBook") is False: continue
        for token in tokens[:2]:
            try:
                book=fetch_p(token)
                report["book_probes"].append({"venue":"polymarket",
                    "token_id":token,"book_returned":True,
                    "ask_levels":len(book.get("asks",[])),
                    "best_ask":str(polymarket_buy_levels(book)[0][0]) if polymarket_buy_levels(book) else None})
            except (ValueError,HTTPError,URLError,TimeoutError) as e:
                report["errors"].append({"venue":"polymarket","token_id":token,
                    "kind":type(e).__name__,"http_status":getattr(e,"code",None)})
    if not (k and p):
        report["status"]="EVENT_DISCOVERY_INCOMPLETE"
    elif any(err.get("venue")=="polymarket" and err.get("http_status")==403 for err in report["errors"]):
        report["status"]="POLYMARKET_ORDERBOOK_ACCESS_DENIED_403"
    elif not any(b.get("venue")=="polymarket" for b in report["book_probes"]):
        report["status"]="NO_POLYMARKET_PUBLIC_ORDERBOOKS_RETURNED"
    else:
        report["status"]="BOOK_PROBE_ONLY_RULES_UNVERIFIED"
    report["price_evidence"]="CLOB order-book asks required for executable costing; Gamma outcomePrices, if present, are indicative only."
    report["clob_access_diagnosis"]="HTTP 403 indicates access refused; not evidence of empty order books. Do not use alternative networks, identities or endpoints to evade an access restriction."
    report["requires_manual_followup"]=["Check legitimate CLOB public access through official support/documentation","Verify settlement and postponement differences","Verify fee and FX schedules before net ROI"]
    report["paper_net_roi_calculable"]=False
    report["polymarket_international_execution_eligible_for_bc_resident"]=False
    report["venue_scope"]="Public research only. Polymarket International excluded as an executable venue for BC-based deployment."
    report["warning"]="No verified fee-adjusted net ROI or tradable arbitrage. If CLOB HTTP 403 persists, do not bypass access restrictions."
    return report

def main():
    path=Path("one_event_discovery.json")
    evidence=json.loads(path.read_text(encoding="utf-8"))
    result=inspect(evidence)
    Path("one_event_book_probe.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"kalshi_contracts":len(result["kalshi_contracts"]),
        "polymarket_contracts":len(result["polymarket_contracts"]),
        "book_probes":len(result["book_probes"]),"errors":result["errors"],
        "rule_equivalence_verified":False}))
if __name__=="__main__":
    main()
