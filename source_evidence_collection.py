"""Read-only primary market metadata collection for mapped arbitrage pairs.

Never infers settlement equivalence or an executable fee from a source field.
"""
import json
from datetime import datetime, timezone
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

KALSHI = "https://api.elections.kalshi.com/trade-api/v2/markets/"
GAMMA = "https://gamma-api.polymarket.com/markets"
POLY_FEE = "https://clob.polymarket.com/fee-rate"


def _get(url, opener):
    req = Request(url, headers={"Accept": "application/json",
                                "User-Agent": "CJ-Arbitrage-Research/0.5"})
    with opener(req, timeout=20) as response:
        return json.load(response)


def _tokens(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return [str(x) for x in value] if isinstance(value, list) else []


def collect_pair(ticker, token, *, opener=urlopen):
    """Collect source-linked evidence; fail closed on mismatched token IDs."""
    if not ticker or not token or "/" in ticker or not str(token).isdigit():
        raise ValueError("Invalid market identifiers")
    ticker, token = str(ticker), str(token)
    k_url = KALSHI + quote(ticker, safe="")
    p_url = GAMMA + "?" + urlencode({"clob_token_ids": token, "limit": 20})
    fee_url = POLY_FEE + "?" + urlencode({"token_id": token})
    record = {"kalshi_market_id": ticker, "polymarket_token_id": token,
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "research_only": True, "trade_allowed": False,
              "settlement_equivalence_verified": False,
              "fees_verified_for_execution": False,
              "source_urls": {"kalshi": k_url, "polymarket": p_url,
                              "polymarket_fee": fee_url},
              "issues": []}
    try:
        raw = _get(k_url, opener)
        market = raw.get("market", {}) if isinstance(raw, dict) else {}
        if market.get("ticker") != ticker:
            raise ValueError("Kalshi ticker mismatch")
        record["kalshi_rules_primary"] = market.get("rules_primary")
        record["kalshi_rules_secondary"] = market.get("rules_secondary")
        record["kalshi_fee_schedule"] = market.get("fee_waiver_expiration_time")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        record["issues"].append("Kalshi evidence unavailable: " + type(exc).__name__)
    try:
        raw = _get(p_url, opener)
        matches = [m for m in raw if token in _tokens(m.get("clobTokenIds"))] if isinstance(raw, list) else []
        if len(matches) != 1:
            raise ValueError("Polymarket token match not unique")
        market = matches[0]
        record["polymarket_market_id"] = str(market.get("id"))
        record["polymarket_description"] = market.get("description")
        record["polymarket_resolution_source"] = market.get("resolutionSource")
        record["polymarket_fee_schedule_metadata"] = market.get("feeSchedule")
        record["polymarket_fees_enabled"] = market.get("feesEnabled")
        record["polymarket_event_url"] = ("https://polymarket.com/event/" + market["slug"]) if market.get("slug") else None
    except (ValueError, OSError, KeyError, TypeError) as exc:
        record["issues"].append("Polymarket evidence unavailable: " + type(exc).__name__)
    try:
        fee = _get(fee_url, opener)
        if not isinstance(fee, dict):
            raise ValueError("Invalid fee response")
        record["polymarket_fee_api_raw"] = fee
    except (ValueError, OSError, KeyError, TypeError) as exc:
        record["issues"].append("Polymarket fee unavailable: " + type(exc).__name__)
    record["status"] = "SOURCE_FIELDS_COLLECTED_REVIEW_REQUIRED" if not record["issues"] else "SOURCE_EVIDENCE_INCOMPLETE"
    return record
