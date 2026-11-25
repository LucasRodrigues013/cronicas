import base64,hashlib,unittest
from worldroot.private_github import GitHubREST
from worldroot.ledger import GateError
class RetrievalRouterTests(unittest.TestCase):
    def fake(self,body,large=True,bad=False):
        sha=hashlib.sha1(b"blob "+str(len(body)).encode()+b"\0"+body).hexdigest()
        api=GitHubREST("owner/repo",token="fixture")
        calls=[]
        def request(verb,path):
            calls.append(path)
            if path.startswith("/contents/"):
                return {"type":"file","sha":sha,"size":len(body),"encoding":"none" if large else "base64","content":"" if large else base64.b64encode(body).decode()}
            return {"sha":sha,"encoding":"base64","content":base64.b64encode(b"bad" if bad else body).decode()}
        api._request=request
        return api,calls
    def test_fallback(self):
        a,c=self.fake(b"large text")
        self.assertEqual(a.get("history/source")["bytes"],b"large text")
        self.assertEqual(len(c),2)
    def test_no_fallback_for_valid_or_real_empty(self):
        for body in (b"ok",b""):
            a,c=self.fake(body,False)
            self.assertEqual(a.get("file")["bytes"],body)
            self.assertEqual(len(c),1)
    def test_invalid_blob_fails_closed(self):
        a,c=self.fake(b"source",True,True)
        with self.assertRaises(GateError):a.get("file")
