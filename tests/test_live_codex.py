import hashlib
import sqlite3
import unittest
from worldroot.live_codex import initialize, apply_delta, current, aliases, jsonstr, SCHEMA

class LiveCodexTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        initialize(self.db)
        for name,domains in (("lucas",["Personagens"]),("miren",["Personagens"]),("torre",["Ambientes"]),("casa",["Ambientes"]),("cajado-1",["Arsenal"]),("spell",["Magia e poderes"])):
            self.db.execute("INSERT INTO records VALUES(?,?,?)",("assets",name,jsonstr({"id":name,"name":name,"domains":domains})))
        self.db.commit()
        self.prose="Lucas chegou à Torre.\nLucas recebeu o cajado.\nLucas guardou o cajado na Torre.\nMiren recebeu o cajado.\nMiren conjurou a técnica.\n"
        self.sha=hashlib.sha256(self.prose.encode()).hexdigest()
    def tearDown(self):
        self.db.close()
    def event(self,kind,entity,line,value,day=580):
        return {"kind":kind,"entity_id":entity,"line":line,"anchor":self.prose.splitlines()[line-1],"value":value,"day":day,"clock":"12h00","scope":"WORLD"}
    def delta(self,events,episode="ep580"):
        return {"schema":SCHEMA,"episode":episode,"prose_sha256":self.sha,"events":events,"new_entities":[],"unresolved":[]}
    def apply(self,d,sequence=51):
        return apply_delta(self.db,d,self.prose,sequence,580,self.sha,{"spell"})
    def test_acquisition_storage_transfer_and_cast(self):
        d=self.delta([self.event("APPEARANCE","lucas",1,{"location_id":"torre"}),self.event("ACQUIRE","lucas",2,{"item_id":"cajado-1"}),self.event("STORE","lucas",3,{"item_id":"cajado-1","location_id":"torre"}),{**self.event("ACQUIRE","miren",4,{"item_id":"cajado-1"}),"location_id":"torre"},self.event("LEARN","miren",5,{"spell_id":"spell","method":"explicit synthetic learning fixture"}),self.event("CAST","miren",5,{"spell_id":"spell"})])
        self.assertEqual(self.apply(d),"APPLIED")
        self.assertEqual(current(self.db,"cajado-1","custody")["holder"],"miren")
        self.assertEqual(current(self.db,"lucas","last_observed_location"),"torre")
        self.assertIsNotNone(current(self.db,"miren","last_cast:spell"))
        self.assertIsNotNone(current(self.db,"miren","learned:spell"))
        self.assertEqual(self.apply(d),"IDEMPOTENT")
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events").fetchone()[0],6)
    def test_custody_conflict_rolls_back(self):
        d=self.delta([self.event("ACQUIRE","lucas",2,{"item_id":"cajado-1"}),self.event("ACQUIRE","miren",4,{"item_id":"cajado-1"})])
        with self.assertRaises(ValueError):self.apply(d)
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events").fetchone()[0],0)
        self.assertIsNone(current(self.db,"cajado-1","custody"))
    def test_literal_and_unknown_item_rejected(self):
        e=self.event("ACQUIRE","lucas",2,{"item_id":"cajado-1"});e["anchor"]="inventado"
        with self.assertRaises(ValueError):self.apply(self.delta([e]))
        with self.assertRaises(ValueError):self.apply(self.delta([self.event("ACQUIRE","lucas",2,{"item_id":"inexistente"})]))
    def test_closed_delta_immutable(self):
        self.apply(self.delta([self.event("APPEARANCE","lucas",1,{"location_id":"torre"})]))
        with self.assertRaises(ValueError):self.apply(self.delta([]))
    def test_location_not_overwritten_by_older_observation(self):
        self.apply(self.delta([self.event("APPEARANCE","lucas",1,{"location_id":"torre"}),self.event("APPEARANCE","lucas",1,{"location_id":"casa"},day=579)]))
        self.assertEqual(current(self.db,"lucas","last_observed_location"),"torre")
    def test_exact_identity_and_domain(self):
        rows=[{"id":"aerun-instituto","name":"AERÚN","domains":["Organizações"]},{"id":"aerun-guardiao","name":"AERÚN","domains":["Bestiário"]}]
        self.assertEqual(len(aliases(rows,"AERUN")),2)
        self.assertEqual([r["id"] for r in aliases(rows,"AERUN",domain="Bestiário")],["aerun-guardiao"])
        self.assertEqual([r["id"] for r in aliases(rows,"AERUN",entity="aerun-instituto")],["aerun-instituto"])

    def test_catalog_is_not_personal_repertoire(self):
        with self.assertRaisesRegex(ValueError,"Unproven personal spell"):
            self.apply(self.delta([self.event("CAST","miren",5,{"spell_id":"spell"})]))
        self.assertEqual(self.db.execute("SELECT count(*) FROM codex_events").fetchone()[0],0)
    def test_old_item_mention_is_not_access(self):
        e=self.event("USE_ITEM","lucas",2,{"item_id":"cajado-1","method":"exame"})
        with self.assertRaisesRegex(ValueError,"Item access"):
            self.apply(self.delta([e]))
    def test_stored_item_cannot_teleport(self):
        d=self.delta([self.event("ACQUIRE","lucas",2,{"item_id":"cajado-1"}),self.event("STORE","lucas",3,{"item_id":"cajado-1","location_id":"torre"}),{**self.event("ACQUIRE","miren",4,{"item_id":"cajado-1"}),"location_id":"casa"}])
        with self.assertRaisesRegex(ValueError,"actual location"):
            self.apply(d)
        self.assertIsNone(current(self.db,"cajado-1","custody"))
    def test_storage_does_not_change_owner(self):
        d=self.delta([self.event("ACQUIRE","lucas",2,{"item_id":"cajado-1","ownership_transfer":True}),self.event("STORE","lucas",3,{"item_id":"cajado-1","location_id":"torre"})])
        self.apply(d)
        v=current(self.db,"cajado-1","custody")
        self.assertEqual(v["owner"],"lucas")
        self.assertIsNone(v["holder"])
        self.assertEqual(v["location"],"torre")
