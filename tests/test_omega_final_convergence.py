import sqlite3,unittest
from worldroot import live_codex as codex
from worldroot.omega_final_convergence import reconcile,install,lookup,graph_fingerprint

def row(ident,labels,visibility="WORLD_NO_CHARACTER_INJECTION",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",role="Response"):
    return dict(id=ident,macro=1,source="source",interval=[1,2],entities=labels,visibility=visibility,authority=authority,role=role,axes=[1],disposition="PENDING_ATOMIC_REVIEW",promotion=False)
class Convergence(unittest.TestCase):
    def setUp(self):
        self.records=[dict(id="a",name="Name",aliases=["Alias"]),dict(id="b",name="Name",aliases=[])]
        self.rows=[row("g1",["Name","Alias","Unknown"]),row("g2",["Name"],"READER_ONLY_NO_CHARACTER_INJECTION"),row("g3",[])]
        self.db=sqlite3.connect(":memory:");codex.initialize(self.db)
        self.db.executemany("INSERT INTO records VALUES(?,?,?)",[("Personagens",r["id"],"{}") for r in self.records]);self.db.commit()
    def tearDown(self):self.db.close()
    def test_candidates(self):
        rows,links=reconcile(self.rows,self.records,{"g1"})
        self.assertEqual(len(links),5)
        self.assertEqual([x["status"] for x in rows[0]["labels"]],["SINGLE_CANDIDATE","AMBIGUOUS","UNMATCHED"])
        self.assertFalse(rows[0]["identity_resolved"]);self.assertFalse(rows[1]["knowledge_injection"])
        self.assertEqual(rows[1]["review_route"],"CRITICAL_SCOPE")
        self.assertTrue(rows[0]["editorially_prepared"]);self.assertFalse(rows[2]["editorially_prepared"])
    def test_readback_and_replay(self):
        rows,links=reconcile(self.rows,self.records,{"g1"})
        before=graph_fingerprint(self.db)
        for _ in range(2):
            self.assertEqual(install(self.db,rows,links,"binding","inventory"),before)
            self.assertEqual(lookup(self.db,group_id="g1",editorial=True),[rows[0]])
            self.assertEqual(len(lookup(self.db,candidate_id="a",editorial=True)),2)
            self.assertEqual(len(lookup(self.db,source="source",editorial=True)),3)
            self.assertEqual(graph_fingerprint(self.db),before)
    def test_denied(self):
        rows,links=reconcile(self.rows,self.records,set());install(self.db,rows,links,"binding","inventory")
        with self.assertRaises(ValueError):lookup(self.db,candidate_id="a")
        with self.assertRaises(ValueError):lookup(self.db,group_id="g1",candidate_id="a",editorial=True)
    def test_invalid_inventory(self):
        with self.assertRaises(ValueError):reconcile(self.rows,self.records,{"missing"})
        with self.assertRaises(ValueError):reconcile(self.rows+[self.rows[0]],self.records,set())
        with self.assertRaises(ValueError):reconcile([dict(self.rows[0],promotion=True)],self.records,set())
