import unittest,sqlite3,json,hashlib
from worldroot.r36_temporal import public_anchor_rows,rank_public_anchors,combine_anchor_lane
from worldroot.live_codex import initialize,field_review_inventory
from worldroot.r36_history_advisory import words
class Epistemic(unittest.TestCase):
    def fixture(self):
        prose="A praça recebeu o selo.\nA chave secreta foi entregue.\nA ponte abriu ao povo.\nO segredo permaneceu.\nO navio partiu."
        def ev(i,n,anchor,vis="PUBLICO",clock="08h00"):
            return {"event_id":i,"visibility":vis,"clock":clock,"occurred_day":10,"source":{"sha256":"sha","line":n,"literal_anchor":anchor}}
        c={"episode_id":"ep","sequence":1,"metadata":{"day":10},"story_sha256":"sha","events":[ev("a",1,"praça recebeu"),ev("b",2,"chave secreta","PRIVADO_PERSONAGEM"),ev("c",3,"ponte abriu"),ev("d",4,"segredo permaneceu"),ev("e",4,"segredo","BASTIDORES"),ev("f",5,"navio partiu",clock="12h00")]}
        return c,{"sequence":1,"day":10,"hour":"10h00"},lambda ep:(prose,"sha")
    def test_public_exact_and_temporal(self):
        c,h,lookup=self.fixture();r=public_anchor_rows([c],h,lookup)
        self.assertEqual([x["event_id"] for x in r],["a","c"])
        a=rank_public_anchors(r,words("ponte abriu"))
        self.assertEqual(len(a),1);self.assertEqual(a[0]["line"],3)
        self.assertNotIn("anchor",a[0]);self.assertFalse(a[0]["knowledge_injection"])
        self.assertEqual(a[0]["anchor_sha256"],hashlib.sha256("ponte abriu".encode()).hexdigest())
    def test_no_adjacent_or_single_token(self):
        c,h,lookup=self.fixture();r=public_anchor_rows([c],h,lookup)
        self.assertEqual(rank_public_anchors(r,words("chave secreta")),[])
        self.assertEqual(rank_public_anchors(r,words("ponte povo")),[])
    def test_source_tampering(self):
        c,h,lookup=self.fixture()
        with self.assertRaises(ValueError):public_anchor_rows([c],h,lambda ep:("wrong","sha"))
        with self.assertRaises(ValueError):public_anchor_rows([c],h,lambda ep:("wrong","changed"))
    def test_unknown_clock_same_day(self):
        c,h,lookup=self.fixture();c["events"][0]["clock"]=None
        self.assertEqual([x["event_id"] for x in public_anchor_rows([c],h,lookup)],["c"])
    def test_combined_budget_and_duplicates(self):
        base=[{"source":"ep","line":i} for i in (1,2,3)]
        a=[{"episode":"ep","line":3},{"episode":"ep","line":5}]
        self.assertEqual(combine_anchor_lane(base,a),base[:2]+[a[1]])
        self.assertEqual(combine_anchor_lane(base,a[:1]),base)
        self.assertEqual(combine_anchor_lane([],a),a[:1])
    def test_field_unknown_and_private(self):
        r={"id":"person","domains":["Personagens"],"natural_profile":{"fields":{"hair":{"status":"RECUPERADO","value":"dark"},"eyes":{"status":"PENDENTE_FONTE","value":"unknown"},"goals":{"status":"SEGREDO","scope":"AUTHOR_ONLY","value":"secret"},"knowledge":{"status":"RECUPERADO","value":"secret"}}}}
        out=field_review_inventory(r);f=out["fields"]
        self.assertEqual(f["hair"]["status"],"EDITORIAL_REFERENCE_NOT_CURRENT_STATE")
        self.assertEqual(f["eyes"]["status"],"UNKNOWN_OR_PENDING_SOURCE")
        self.assertNotIn("goals",f);self.assertNotIn("knowledge",f)
        self.assertNotIn("value",f["hair"]);self.assertFalse(f["hair"]["current_confirmed"])
    def test_field_conflict_and_no_write(self):
        db=sqlite3.connect(":memory:");initialize(db)
        r={"id":"person","domains":["Personagens"],"natural_profile":{"fields":{"hair":{"status":"RECUPERADO","value":"dark"}}}}
        db.execute("INSERT INTO records VALUES(?,?,?)",("Personagens","person","{}"))
        for i,scope,field,value in [(0,"WORLD","hair","light"),(1,"PRIVATE_CHARACTER","fears","private"),(2,"WORLD","knowledge:x","secret")]:
            eid="ep:"+str(i);db.execute("INSERT INTO codex_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(eid,"ep",1,i,10,"09h00","person","ATTRIBUTE",json.dumps({"scope":scope}),"sha",1,"anchor"))
            db.execute("INSERT INTO codex_state VALUES(?,?,?,?)",("person",field,json.dumps(value),eid))
        before=list(db.iterdump());out=field_review_inventory(r,db)
        self.assertEqual(out["fields"]["hair"]["status"],"MULTIPLE_VALUES_REVIEW")
        self.assertEqual(out["fields"]["fears"]["status"],"UNKNOWN_OR_PENDING_SOURCE")
        self.assertNotIn("knowledge:x",out["fields"]);self.assertEqual(before,list(db.iterdump()));db.close()
