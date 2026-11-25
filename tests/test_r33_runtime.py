import unittest,tempfile,concurrent.futures,hashlib
from pathlib import Path
from unittest.mock import patch
from worldroot.r33_runtime import persist,preparation,verify_submission,REVIEWS,digest
from worldroot.memory_continuity import DOMAINS
from worldroot.curated_memory import search_cards
class TestR33(unittest.TestCase):
    def test_concurrent_identical_preparation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"prep.json"
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
                out=list(ex.map(lambda _:persist(p,{"data":1}),range(128)))
            self.assertEqual(out.count("CREATED"),1);self.assertEqual(out.count("IDEMPOTENT"),127)
    def test_concurrent_conflicting_preparation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"prep.json"
            def attempt(i):
                try:return persist(p,{"i":i})
                except ValueError:return "REJECTED"
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:out=list(ex.map(attempt,range(128)))
            self.assertEqual(out.count("CREATED"),1);self.assertEqual(out.count("REJECTED"),127)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"prep.json";target=Path(d)/"outside";target.write_text("untouched");p.symlink_to(target)
            with self.assertRaises(ValueError):persist(p,{"data":1})
            self.assertEqual(target.read_text(),"untouched")
    def test_prepare_missing_critical(self):
        with tempfile.TemporaryDirectory() as d,patch("worldroot.r33_runtime.author_context",return_value={}):
            with self.assertRaises(ValueError):preparation(Path(d),{"episode_id":"OLD-001"},"NEW-001",[],{}, {}, [])
    def test_prepare_rejects_unmapped_facts(self):
        req=[{"id":"a","query":"Miren","domain":"identity","critical":True}]
        domains={k:{"applicable":k=="identity","reason":"reviewed"} for k in DOMAINS}
        with tempfile.TemporaryDirectory() as d,patch("worldroot.r33_runtime.author_context",return_value={}):
            with self.assertRaises(ValueError):preparation(Path(d),{"episode_id":"OLD-001"},"NEW-001",req,{},domains,[{"scene":1,"purpose":"test","ids":["b"]}])
    def test_prepare_rejects_low_recall(self):
        req=[{"id":"a","query":"Miren","domain":"identity","critical":True}]
        domains={k:{"applicable":k=="identity","reason":"reviewed"} for k in DOMAINS}
        with tempfile.TemporaryDirectory() as d,patch("worldroot.r33_runtime.author_context",return_value={}),patch("worldroot.r33_runtime.review_creation",return_value={"status":"RECOVER_BEFORE_RELEASE"}):
            with self.assertRaises(ValueError):preparation(Path(d),{"episode_id":"OLD-001"},"NEW-001",req,{},domains,[{"scene":1,"purpose":"test","ids":["a"]}])
    def test_submission_missing_preparation(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):verify_submission(Path(d),{},{"delivery_id":"NEW-001"})
    def test_submission_tampered_preparation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"preparations"/"NEW-001.json";persist(p,{"head":{},"project":"CRONICAS_DE_UM_NOVO_MUNDO","delivery_id":"NEW-001","preparation_sha256":"wrong"})
            with self.assertRaises(ValueError):verify_submission(Path(d),{},{"delivery_id":"NEW-001"})
    def test_curated_role_separation(self):
        c=[{"card":"a","metadata":"Miren cabelos","anchor":"cabelos escuros","role":"Response"},{"card":"b","metadata":"Miren cabelos","anchor":"cabelos claros","role":"Prompt"}]
        self.assertEqual([x["card"] for x in search_cards(c,"Miren cabelo",role="Response")],["a"])
        self.assertEqual(search_cards(c,"zzzzqzx"),[])
if __name__=="__main__":unittest.main()
