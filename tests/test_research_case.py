import unittest
from research_case import evaluate_research_case
from rule_dossier import FIELDS

def dossier(side):
    result = {key:"same terms" for key in FIELDS}
    result.update(observation_start_utc="2026-10-28T12:00:00Z",
                  observation_end_utc="2026-10-28T13:00:00Z",
                  payout_per_contract="1", official_rule_url="https://example.com/rules",
                  verified_by_human=True, selected_side=side)
    return result

def case():
    return dict(
        rules_a=dossier("YES"), rules_b=dossier("NO"),
        kalshi_book={"orderbook_fp":{"no_dollars":[["0.61","100"]]}},
        polymarket_book={"asks":[{"price":"0.50","size":"100"}]},
        observed_kalshi="2026-10-28T12:00:00Z",
        observed_polymarket="2026-10-28T12:00:01Z",
        fee_kalshi="0.01", fee_polymarket="0.01", other_cost_usd="0",
        kalshi_side="YES", polymarket_side="NO",
        kalshi_ticker="DEMO", polymarket_token_id="123")

class ResearchCaseTests(unittest.TestCase):
    def test_matching_manual_dossier_is_still_nonactionable(self):
        result=evaluate_research_case(case())
        self.assertEqual(result["status"],"PAPER_CANDIDATE_REQUIRES_VERIFICATION")
        self.assertFalse(result["verified_arbitrage"])
        self.assertFalse(result["trade_allowed"])
        self.assertIsNone(result["realized_profit_usd"])
    def test_different_event_rules_block_prices(self):
        obj=case()
        obj["rules_b"]["resolution_condition"]="different outcome"
        result=evaluate_research_case(obj)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertIsNone(result["displayed_depth_review"])
    def test_wrong_book_side_blocks(self):
        obj=case()
        obj["polymarket_side"]="YES"
        self.assertEqual(evaluate_research_case(obj)["status"],"BLOCKED")
    def test_missing_fees_block(self):
        obj=case()
        obj["fee_kalshi"]=None
        self.assertEqual(evaluate_research_case(obj)["status"],"BLOCKED")
    def test_missing_rules_block(self):
        self.assertEqual(evaluate_research_case({})["status"],"BLOCKED")
if __name__=="__main__":
    unittest.main()
