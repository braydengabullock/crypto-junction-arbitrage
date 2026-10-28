import unittest
from sports_discovery_funnel import funnel

class DiscoveryFunnelTests(unittest.TestCase):
    def test_counts_distinct_events_and_unmapped_sides(self):
        a="KXNBAGAME-26OCT28OKCDAL-OKC"
        b="KXNBAGAME-26OCT28OKCDAL-DAL"
        k={"markets":[{"ticker":a},{"ticker":b}]}
        p={"markets":[{"id":"1"}],"data_quality":{"pagination":{"complete":False}}}
        matches={"candidate_limit":500,"candidates":[{"kalshi_ticker":a,"match_method":"sports_identifier_date_teams_research"},
                                                {"kalshi_ticker":b,"match_method":"sports_identifier_date_teams_research"}]}
        mapping={"opposing_token_map":{a+"|YES":"123"}}
        r=funnel(k,p,matches,mapping)
        self.assertEqual(r["by_league"]["NBA"]["kalshi_distinct_events_discovered"],1)
        self.assertEqual(r["by_league"]["NBA"]["strict_opposing_token_mapped_sides"],1)
        self.assertEqual(r["by_league"]["NBA"]["identifier_matched_but_unmapped_sides"],1)
        self.assertFalse(r["matches_candidate_cap_reached"])
        self.assertEqual(r["verified_opportunities"],0)
    def test_unrelated_mapping_does_not_inflate_coverage(self):
        a="KXNBAGAME-26OCT28OKCDAL-OKC"
        b="KXNBAGAME-26OCT28OKCDAL-DAL"
        unrelated="KXNBAGAME-26OCT29BOSNYK-BOS"
        k={"markets":[{"ticker":a},{"ticker":b}]}
        matches={"candidate_limit":500,"candidates":[
            {"kalshi_ticker":a,"match_method":"sports_identifier_date_teams_research"},
            {"kalshi_ticker":b,"match_method":"sports_identifier_date_teams_research"}]}
        mapping={"opposing_token_map":{a+"|YES":"123", unrelated+"|YES":"456"}}
        r=funnel(k,{"markets":[]},matches,mapping)["by_league"]["NBA"]
        self.assertEqual(r["strict_opposing_token_mapped_sides"],1)
        self.assertEqual(r["identifier_matched_but_unmapped_sides"],1)
        self.assertEqual(r["identifier_matched_but_unmapped_events"],1)
        self.assertEqual(r["mapping_coverage_pct_of_matched_sides"],50.0)

    def test_orphan_candidates_and_empty_mapping_are_excluded(self):
        a="KXNBAGAME-26OCT28OKCDAL-OKC"
        orphan="KXNBAGAME-26OCT29BOSNYK-BOS"
        k={"markets":[{"ticker":a}]}
        matches={"candidate_limit":500,"candidates":[
            {"kalshi_ticker":a,"match_method":"sports_identifier_date_teams_research"},
            {"kalshi_ticker":orphan,"match_method":"sports_identifier_date_teams_research"}]}
        mapping={"opposing_token_map":{a+"|YES":"",orphan+"|YES":"token"}}
        r=funnel(k,{"markets":[]},matches,mapping)["by_league"]["NBA"]
        self.assertEqual(r["exact_identifier_matched_sides"],1)
        self.assertEqual(r["strict_opposing_token_mapped_sides"],0)
        self.assertEqual(r["identifier_matched_but_unmapped_sides"],1)
        self.assertEqual(r["discovery_bottleneck"],"TOKEN_MAPPING")

    def test_bottleneck_identifies_missing_match_and_downstream_review(self):
        a="KXNBAGAME-26OCT28OKCDAL-OKC"
        k={"markets":[{"ticker":a}]}
        p={"markets":[]}
        empty=funnel(k,p,{"candidate_limit":500,"candidates":[]},{"opposing_token_map":{}})
        self.assertEqual(empty["by_league"]["NBA"]["discovery_bottleneck"],"IDENTIFIER_MATCHING")
        matches={"candidate_limit":500,"candidates":[
            {"kalshi_ticker":a,"match_method":"sports_identifier_date_teams_research"}]}
        mapped=funnel(k,p,matches,{"opposing_token_map":{a+"|YES":"token"}})
        self.assertEqual(mapped["by_league"]["NBA"]["discovery_bottleneck"],"DOWNSTREAM_PRICE_AND_RULE_REVIEW")
        self.assertEqual(mapped["by_league"]["NBA"]["identifier_coverage_pct_of_discovered_sides"],100.0)
        self.assertEqual(mapped["verified_opportunities"],0)

    def test_research_priorities_rank_actual_coverage_losses(self):
        n1="KXNBAGAME-26OCT28OKCDAL-OKC"
        n2="KXNBAGAME-26OCT28OKCDAL-DAL"
        h1="KXNHLGAME-26OCT28BOSTOR-BOS"
        k={"markets":[{"ticker":n1},{"ticker":n2},{"ticker":h1}]}
        matches={"candidate_limit":500,"candidates":[
            {"kalshi_ticker":n1,"match_method":"sports_identifier_date_teams_research"}]}
        r=funnel(k,{"markets":[]},matches,{"opposing_token_map":{}})
        self.assertEqual(r["research_priorities"],[
            {"league":"NBA","stage":"IDENTIFIER_MATCHING","missing_sides":1,
             "note":"Research coverage only; not a verified executable opportunity"},
            {"league":"NBA","stage":"TOKEN_MAPPING","missing_sides":1,
             "note":"Research coverage only; not a verified executable opportunity"},
            {"league":"NHL","stage":"IDENTIFIER_MATCHING","missing_sides":1,
             "note":"Research coverage only; not a verified executable opportunity"}])
        self.assertEqual(r["verified_opportunities"],0)

    def test_warning_reflects_actual_cap_and_incomplete_collection(self):
        r=funnel({"markets":[]},{"markets":[],"data_quality":{"pagination":{"complete":False}}},
                 {"candidate_limit":2,"candidates":[{},{}]},{"opposing_token_map":{}})
        self.assertIn("cap of 2",r["warning"])
        self.assertIn("collection is incomplete",r["warning"])
        self.assertTrue(r["matches_candidate_cap_reached"])
        self.assertFalse(r["verified_opportunities"])

    def test_complete_uncapped_collection_does_not_warn_about_truncation(self):
        r=funnel({"markets":[]},{"markets":[],"data_quality":{"pagination":{"complete":True}}},
                 {"candidate_limit":500,"candidates":[]},{"opposing_token_map":{}})
        self.assertNotIn("truncated",r["warning"])
        self.assertNotIn("collection is incomplete",r["warning"])
        self.assertFalse(r["matches_candidate_cap_reached"])
    def test_candidate_cap_detection_uses_configured_limit(self):
        r=funnel({"markets":[]},{"markets":[]},{"candidate_limit":1,"candidates":[{}]},
                 {"opposing_token_map":{}})
        self.assertTrue(r["matches_candidate_cap_reached"])
if __name__=="__main__":
    unittest.main()
