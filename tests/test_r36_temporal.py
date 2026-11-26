import sqlite3,unittest,json
from worldroot.live_codex import initialize
from worldroot.r36_temporal import rebuild,coverage,entity_history

class R36TemporalTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        initialize(self.db)
        for x in ("lucas","item","miren"):
            self.db.execute("INSERT INTO records VALUES(?,?,?)",("assets",x,"{}"))
        for i,scope,clock in [(0,"WORLD","09h00"),(1,"PRIVATE_CHARACTER","09h00"),(2,"WORLD",None),(3,"WORLD","10h00")]:
            eid="ep:"+str(i)
            self.db.execute("INSERT INTO codex_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
              (eid,"ep",1,i,580,clock,"lucas","ACQUIRE",json.dumps({"scope":scope}),"sha",i+1,"anchor"+str(i)))
            self.db.execute("INSERT INTO codex_event_entities VALUES(?,?,?)",(eid,"item","ITEM"))
        self.db.commit()
    def tearDown(self): self.db.close()
    def closure(self):
        return {"episode_id":"ep","sequence":1,"story_sha256":"sha","metadata":{"day":580},
         "events":[{"event_id":"c"+str(i),"visibility":vis,"clock":tm,"occurred_day":580,
          "summary_candidato":"synthetic","source":{"sha256":"sha","line":i+1,"literal_anchor":"anchor"+str(i)}}
          for i,vis,tm in [(0,"PUBLICO","09h00"),(1,"PUBLICO","09h00"),(2,"PUBLICO",None),(3,"BASTIDORES","10h00"),(4,"PUBLICO","10h00")]]}
    def test_coverage_idempotent(self):
        for _ in range(2):
            self.assertEqual(rebuild(self.db,[self.closure()]),{"canonical_events":5,"shared_anchor_events":4,"without_shared_anchor":1,"semantic_certification":False})
    def test_public_before_limit(self):
        rebuild(self.db,[self.closure()])
        rows=entity_history(self.db,"item",580,"09h00",1)
        self.assertEqual([r["event_id"] for r in rows],["ep:0"])
        self.assertEqual(rows[0]["shared_public_source_anchors"],["c0"])
        self.assertEqual(rows[0]["roles"],["ITEM"])
    def test_private_canonical_anchor_excluded(self):
        rebuild(self.db,[self.closure()])
        rows=entity_history(self.db,"item",580)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["shared_public_source_anchors"],[])
    def test_temporal_unknown_future_and_identity(self):
        rebuild(self.db,[self.closure()])
        self.assertEqual(entity_history(self.db,"item",579),[])
        self.assertEqual(entity_history(self.db,"item",580,"08h59"),[])
        with self.assertRaises(ValueError):entity_history(self.db,"unknown",580)
        with self.assertRaises(ValueError):entity_history(self.db,"item",580,"25h00")
    def test_hash_mismatch(self):
        c=self.closure();c["events"][0]["source"]["sha256"]="bad"
        with self.assertRaises(ValueError):rebuild(self.db,[c])
    def test_no_inferred_identity(self):
        rebuild(self.db,[self.closure()])
        self.assertEqual(entity_history(self.db,"miren",580),[])
