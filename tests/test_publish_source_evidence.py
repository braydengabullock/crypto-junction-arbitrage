from publish_source_evidence import build, mapped_pairs


def test_batch_deduplicates_and_limits():
    archive = {"captures": [{"opposing_token_map": {"K|YES": "123", "K|NO": "456"}},
                            {"opposing_token_map": {"K|YES": "123"}}]}
    calls = []
    def fake(ticker, token):
        calls.append((ticker, token))
        return {"status": "SOURCE_FIELDS_COLLECTED_REVIEW_REQUIRED", "trade_allowed": False}
    result = build(archive, limit=1, collector=fake)
    assert len(calls) == 1
    assert result["pairs_attempted"] == 1
    assert result["pairs_verified_executable"] == 0


def test_batch_fails_closed_on_collection_error():
    def broken(*args):
        raise TimeoutError("unavailable")
    result = build({"captures": [{"opposing_token_map": {"K|YES": "123"}}]}, collector=broken)
    assert result["records"][0]["status"] == "SOURCE_EVIDENCE_INCOMPLETE"
    assert result["records"][0]["trade_allowed"] is False
