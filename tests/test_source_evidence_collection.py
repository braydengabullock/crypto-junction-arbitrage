import json
from io import BytesIO
from source_evidence_collection import collect_pair


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_collect_pair_keeps_evidence_unverified():
    def opener(request, timeout=20):
        url = request.full_url
        if "kalshi.com" in url:
            payload = {"market": {"ticker": "K-1", "rules_primary": "Official rule"}}
        elif "gamma-api" in url:
            payload = [{"id": "123", "slug": "event-1",
                        "clobTokenIds": '["987","654"]',
                        "description": "Resolve according to rules"}]
        else:
            payload = {"base_fee": 0}
        return Response(json.dumps(payload).encode())
    result = collect_pair("K-1", "987", opener=opener)
    assert result["status"] == "SOURCE_FIELDS_COLLECTED_REVIEW_REQUIRED"
    assert result["polymarket_market_id"] == "123"
    assert result["polymarket_fee_api_raw"] == {"base_fee": 0}
    assert result["trade_allowed"] is False
    assert result["settlement_equivalence_verified"] is False


def test_mismatched_token_never_claims_complete():
    def opener(request, timeout=20):
        url = request.full_url
        payload = ({"market": {"ticker": "K-1"}} if "kalshi.com" in url
                   else [{"id": "123", "clobTokenIds": '["111"]'}]
                   if "gamma-api" in url else {"base_fee": 0})
        return Response(json.dumps(payload).encode())
    result = collect_pair("K-1", "987", opener=opener)
    assert result["status"] == "SOURCE_EVIDENCE_INCOMPLETE"
    assert result["trade_allowed"] is False
