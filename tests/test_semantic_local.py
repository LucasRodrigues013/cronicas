import json,tempfile,unittest
from pathlib import Path
from worldroot.semantic_queue import jobs
from worldroot.semantic_local import run,revision

class LocalSemanticTest(unittest.TestCase):
    def test_two_model_resume(self):
        row={"source":"episode:x","line":1,"anchor_sha256":"abc","source_sha256":"src","source_status":"CLOSED","day":1,"anchor":"Varo chegou.","context":[{"line":1,"text":"Varo chegou."}],"original_id":1,"entity_id":"varo","field":"location"}
        job=list(jobs([row]))[0];calls=[]
        def fake(path,payload=None):
            if path=="/api/tags":return {"models":[{"name":"a","digest":"a"*64},{"name":"b","digest":"b"*64},{"name":"same","digest":"a"*64}]}
            calls.append(payload["model"])
            return {"done":True,"message":{"content":json.dumps({"source_role":"NARRATED","role_reason":"literal","decisions":[{"original_id":1,"entity_id":"varo","field":"location","verdict":"SUPPORTED","reason":"literal","claim":"Varo chegou","evidence":"Varo chegou.","current_state":False}]})}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"jobs";p.write_text(json.dumps(job)+"\n");o=Path(tmp)/"out"
            result=run(p,o,"a","b",api=fake)
            self.assertEqual(result["new_targets_reviewed"],1)
            self.assertEqual(calls,["a","b"])
            self.assertEqual(run(p,o,"a","b",api=fake)["new_jobs_completed"],0)
            self.assertEqual(calls,["a","b"])
            with self.assertRaises(ValueError):run(p,o,"a","same",api=fake)
            with self.assertRaises(ValueError):revision("cloud",fake)
