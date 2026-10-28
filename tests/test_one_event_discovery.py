import io
import json
import unittest
from one_event_discovery import probe
class Response:
    def __init__(self,d): self.stream=io.BytesIO(json.dumps(d).encode())
    def __enter__(self): return self.stream
    def __exit__(self,*args): return False
class ProbeTests(unittest.TestCase):
    def test_identifiers_are_retrieved_without_verification_claim(self):
        def opener(req,timeout):
            return Response({"markets":[{"ticker":"K"}]} if "/trade-api/" in req.full_url
                            else {"markets":[{"id":"P"}]})
        result=probe(opener=opener)
        self.assertEqual(len(result["sources"]),2)
        self.assertFalse(result["rule_equivalence_verified"])
        self.assertFalse(result["orderbook_depth_verified"])
if __name__=="__main__": unittest.main()
