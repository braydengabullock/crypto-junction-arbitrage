import io,json,unittest
from urllib.error import HTTPError
from clob_access_diagnostic import inspect
class Response:
 def __init__(self): self.status=200
 def __enter__(self): return io.BytesIO(b'{"asks":[]}')
 def __exit__(self,*args):pass
class DiagnosticTests(unittest.TestCase):
 def test_denied_public_host_does_not_claim_bad_token(self):
  def deny(req,timeout):raise HTTPError(req.full_url,403,"Forbidden",{},None)
  a=inspect({"markets":[{"id":"m","clobTokenIds":'["123"]'}]},opener=deny)
  self.assertEqual(a["access_conclusion"],"CLOB_HOST_REFUSES_BOTH_PUBLIC_READ_ENDPOINTS")
  self.assertFalse(a["trading_enabled"])
 def test_works(self):
  a=inspect({"markets":[{"id":"m","clobTokenIds":'["123"]'}]},opener=lambda req,timeout:Response())
  self.assertEqual(a["access_conclusion"],"BOOK_PUBLIC_READ_ACCESSIBLE")
 def test_missing(self):
  self.assertEqual(inspect({"markets":[]})["access_conclusion"],"NO_VALID_TOKEN")
if __name__=="__main__":unittest.main()
