import unittest
from one_event_book_probe import inspect
class InspectionTests(unittest.TestCase):
    def test_probes_books_but_does_not_claim_match(self):
        obj={"sources":{
          "kalshi_event":{"data":{"markets":[{"ticker":"K","title":"Test"}]}},
          "polymarket_event":{"data":{"markets":[{"id":"P","question":"Test",
                 "clobTokenIds":'["123","456"]',"enableOrderBook":True}]}}}}
        r=inspect(obj,fetch_k=lambda _ :{"orderbook_fp":{"yes_dollars":[["0.5","1"]],"no_dollars":[]}},
                  fetch_p=lambda _ :{"asks":[{"price":"0.6","size":"1"}]})
        self.assertEqual(len(r["book_probes"]),3)
        self.assertFalse(r["rule_equivalence_verified"])
        self.assertFalse(r["tradable"])
    def test_missing_event_does_not_invent_contracts(self):
        r=inspect({"sources":{}})
        self.assertEqual(r["book_probes"],[])
        self.assertEqual(r["status"],"EVENT_DISCOVERY_INCOMPLETE")
        self.assertFalse(r["both_event_apis_returned"])
        self.assertFalse(r["tradable"])
if __name__=="__main__": unittest.main()
