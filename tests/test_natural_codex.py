import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from worldroot.natural_codex import (MANIFEST, PROJECT, CHAR_FIELDS, SYNC_SCHEMA, git_blob,
    load_overlay, validate_fields, public_fields, validate_new_character, validate_scene_sync,
    augment_record, extra_records)
from worldroot.live_codex import initialize, graph_rows, jsonstr

def field(value="design",status="COMPLETADO",scope="PROVISIONAL_CONTINUITY"):
    return {"value":value,"status":status,"scope":scope,"origin":{"policy":"fixture"},"justification":"synthetic test only"}
def profile():
    return {k:field("explicit unresolved state","PENDENTE_FONTE") for k in CHAR_FIELDS}
def docs(root,base_raw,base,**kwargs):
    root=Path(root)
    (root/"editorial/registries").mkdir(parents=True)
    (root/"canon").mkdir()
    cp={"day":579,"sequence":1,"episode_id":"fixture","source_sha256":"source"}
    (root/"canon/HEAD.json").write_text(json.dumps(cp))
    c={"schema":"worldroot-r35-natural-completion-v1","project":PROJECT,"registry_blob":git_blob(base_raw),"checkpoint":cp,
       "characters":[{"id":"one","name":"One","fields":profile()},{"id":"two","name":"Two","domains":["Personagens"],"fields":profile()}],
       "alias_decisions":[{"decision":"SEPARAR","alias":"homonym","ids":["one","two"]}]}
    c["characters"][0]["fields"]["voice"]=field("quiet")
    c["characters"][0]["fields"]["origin"]=field("hidden", "SEGREDO", "AUTHOR_ONLY")
    w={"schema":"worldroot-r35-world-overlay-v1","project":PROJECT,"registry_blob":git_blob(base_raw),"checkpoint":cp,
       "records":[{"id":"town","name":"Town","fields":{"purpose":field("market")}}],
       "links":[{"from":"one","to":"town","relation":"OBSERVED","status":"RECUPERADO"}]}
    paths=["editorial/registries/characters.json","editorial/registries/world.json"]
    specs=[]
    for path,d in zip(paths,(c,w)):
        raw=json.dumps(d).encode()
        (root/path).write_bytes(raw)
        specs.append({"path":path,"git_blob":git_blob(raw)})
    m={"schema":"worldroot-r35-living-overlay-manifest-v1","project":PROJECT,"base_registry_blob":git_blob(base_raw),
       "checkpoint":cp,"character_overlay":specs[0],"world_overlay":specs[1],"vetoes":[],
       "rules":{"no_automatic_canon_promotion":True,"require_scene_sync":True},**kwargs}
    (root/MANIFEST).write_text(json.dumps(m))
    return m,c,w

class NaturalCodexTests(unittest.TestCase):
    def test_full_fixture_overlay_and_new_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={"records":[{"id":"one"},{"id":"town"}]};raw=b"base"
            docs(tmp,raw,base)
            o=load_overlay(tmp,raw,base)
            self.assertEqual(o["character_count"],2)
            r=augment_record({"id":"one","name":"One","aliases":[]},o)
            self.assertIn("homonym",r["aliases"])
            self.assertEqual(r["natural_profile"]["fields"]["voice"]["value"],"quiet")
            self.assertNotIn("origin",r["natural_profile"]["fields"])
            self.assertEqual(r["cross_domain_links"][0]["to"],"town")
            self.assertEqual([x["id"] for x in extra_records(o)],["two"])
    def test_no_overlay_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_overlay(tmp,b"base",{}))
    def test_manifest_tamper_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={"records":[{"id":"one"},{"id":"town"}]};raw=b"base"
            m,c,w=docs(tmp,raw,base)
            (Path(tmp)/m["character_overlay"]["path"]).write_text(json.dumps(c,indent=2))
            with self.assertRaisesRegex(ValueError,"identity mismatch"):
                load_overlay(tmp,raw,base)
    def test_wrong_base_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={"records":[{"id":"one"},{"id":"town"}]};docs(tmp,b"base",base)
            with self.assertRaisesRegex(ValueError,"authority mismatch"):
                load_overlay(tmp,b"other",base)
    def test_veto_does_not_rewrite_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={"records":[{"id":"one"},{"id":"town"}]};raw=b"base"
            docs(tmp,raw,base,vetoes=[{"id":"one","field":"voice","reason":"author veto"}])
            o=load_overlay(tmp,raw,base)
            self.assertNotIn("voice",augment_record({"id":"one"},o)["natural_profile"]["fields"])
            self.assertEqual(o["profiles"]["one"]["fields"]["voice"]["value"],"quiet")
    def test_veto_cannot_target_nonprovisional_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            base={"records":[{"id":"one"},{"id":"town"}]};raw=b"base"
            docs(tmp,raw,base,vetoes=[{"id":"one","field":"location","reason":"bad"}])
            with self.assertRaisesRegex(ValueError,"Veto is limited"):
                load_overlay(tmp,raw,base)
    def test_missing_field_or_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"Incomplete"):
            validate_fields({},CHAR_FIELDS)
        f=field();f.pop("origin")
        with self.assertRaisesRegex(ValueError,"Untraceable"):
            validate_fields({"voice":f})
    def test_deduction_requires_distinct_sources(self):
        f=field(status="DEDUZIDO");f["origin"]=[{"line":1},{"line":1}]
        with self.assertRaisesRegex(ValueError,"independent"):
            validate_fields({"voice":f})
        f["origin"]=[{"line":1},{"line":2}]
        self.assertEqual(validate_fields({"voice":f})["voice"]["status"],"DEDUZIDO")
    def test_secret_requires_author_scope(self):
        with self.assertRaisesRegex(ValueError,"author-only"):
            validate_fields({"origin":field("secret","SEGREDO","WORLD")})
    def test_general_retrieval_redacts_nested_previous(self):
        f=field("public");f["previous"]={"value":"secret","scope":"AUTHOR_ONLY"}
        d=public_fields({"voice":f,"knowledge":field("private"),"origin":field("secret","SEGREDO","AUTHOR_ONLY")})
        self.assertEqual(set(d),{"voice"})
        self.assertNotIn("previous",d["voice"])
    def test_new_character_profile_and_secret_redaction(self):
        f=profile()
        f["voice"]=field("dry humor")
        f["origin"]=field("secret","SEGREDO","AUTHOR_ONLY")
        card={"id":"new","name":"New","domains":["Personagens"],"profile":{"fields":f}}
        validate_new_character(card,"New arrived.")
        with sqlite3.connect(":memory:") as db:
            initialize(db)
            db.execute("INSERT INTO records VALUES(?,?,?)",("dossiers","new",jsonstr(card)))
            public=graph_rows(db)[0]
            self.assertNotIn("profile",public)
            self.assertNotIn("origin",public["natural_profile"]["fields"])
            self.assertIn("origin",graph_rows(db,public=False)[0]["profile"]["fields"])
    def test_new_character_false_past_event_rejected(self):
        f=profile();f["history"]=field("invented past")
        with self.assertRaisesRegex(ValueError,"Historical|historical"):
            validate_new_character({"profile":{"fields":f}},"New arrived.")
    def test_new_character_canon_requires_exact_anchor(self):
        f=profile();f["identity"]=field("New","CANONICO","WORLD");f["identity"]["origin"]={"line":1,"anchor":"New arrived."}
        validate_new_character({"profile":{"fields":f}},"New arrived.")
        with self.assertRaisesRegex(ValueError,"Literal evidence"):
            validate_new_character({"profile":{"fields":f}},"Different text.")
    def test_scene_sync_complete(self):
        prose="One arrived.\nOne looked."
        delta={"new_entities":[],"events":[{"line":1},{"line":2}]}
        sync={"schema":SYNC_SCHEMA,"scenes":[{"start_line":1,"end_line":2,
           "mentions":[{"id":"one","disposition":"IDENTIFIED","line":1,"anchor":"One arrived."}],
           "event_ordinals":[0,1],"cross_checks":[{"status":"OK","reason":"fixture"}],"hooks":[]}]}
        self.assertEqual(validate_scene_sync(sync,delta,prose,{"one"})["events"],2)
        sync["scenes"][0]["event_ordinals"]=[0]
        with self.assertRaisesRegex(ValueError,"Incomplete scene"):
            validate_scene_sync(sync,delta,prose,{"one"})
    def test_scene_sync_gap_and_blocker_rejected(self):
        sync={"schema":SYNC_SCHEMA,"scenes":[{"start_line":2,"end_line":2,"mentions":[],"event_ordinals":[],"cross_checks":[],"hooks":[]}]}
        with self.assertRaisesRegex(ValueError,"without gaps"):
            validate_scene_sync(sync,{"new_entities":[],"events":[]},"One.\nTwo.",set())
        sync["scenes"][0]["start_line"]=1
        sync["scenes"][0]["cross_checks"]=[{"status":"ALERT","reason":"impossible route","blocking":True}]
        with self.assertRaisesRegex(ValueError,"Blocking"):
            validate_scene_sync(sync,{"new_entities":[],"events":[]},"One.\nTwo.",set())
    def test_scene_sync_requires_profile_for_new_character(self):
        sync={"schema":SYNC_SCHEMA,"scenes":[{"start_line":1,"end_line":1,"mentions":[],"event_ordinals":[],"cross_checks":[],"hooks":[]}]}
        with self.assertRaisesRegex(ValueError,"complete Codex profile"):
            validate_scene_sync(sync,{"new_entities":[{"id":"new","domains":["Personagens"]}],"events":[]},"New.",set())

    def test_typed_event_visible_from_all_affected_entities(self):
        from worldroot.live_codex import apply_delta, events_for_entity, SCHEMA
        prose="One gave the tool to Two in Town."
        sha=hashlib.sha256(prose.encode()).hexdigest()
        with sqlite3.connect(":memory:") as db:
            initialize(db)
            for ident,domain in (("one","dossiers"),("two","dossiers"),("tool","assets"),("town","assets")):
                db.execute("INSERT INTO records VALUES(?,?,?)",(domain,ident,jsonstr({"id":ident,"name":ident,"domains":["Personagens"] if domain=="dossiers" else ["Arsenal"],"aliases":[]})))
            db.commit()
            events=[
                {"kind":"ACQUIRE","entity_id":"one","day":1,"scope":"WORLD","line":1,"anchor":prose,"value":{"item_id":"tool","ownership_transfer":True}},
                {"kind":"TRANSFER","entity_id":"one","day":1,"scope":"WORLD","line":1,"anchor":prose,"location_id":"town","value":{"item_id":"tool","to_id":"two","ownership_transfer":True}}]
            delta={"schema":SCHEMA,"episode":"fixture","prose_sha256":sha,"events":events,"new_entities":[],"unresolved":[]}
            apply_delta(db,delta,prose,1,1,sha,set())
            for ident in ("one","two","tool","town"):
                self.assertEqual(events_for_entity(db,ident)[0]["event_id"],"fixture:1")
            self.assertEqual(events_for_entity(db,"two")[0]["roles"],["RECIPIENT"])
            self.assertEqual(db.execute("SELECT count(*) FROM codex_events").fetchone()[0],2)
            db.execute("DELETE FROM codex_event_entities")
            db.commit()
            self.assertEqual(apply_delta(db,delta,prose,1,1,sha,set()),"IDEMPOTENT")
            self.assertEqual(events_for_entity(db,"town")[0]["event_id"],"fixture:1")

    def test_cross_entity_event_does_not_leak_private_scope(self):
        from worldroot.live_codex import apply_delta, events_for_entity, SCHEMA
        prose="One privately told Two."
        sha=hashlib.sha256(prose.encode()).hexdigest()
        with sqlite3.connect(":memory:") as db:
            initialize(db)
            for ident in ("one","two"):
                db.execute("INSERT INTO records VALUES(?,?,?)",("dossiers",ident,jsonstr({"id":ident,"name":ident,"domains":["Personagens"],"aliases":[]})))
            db.commit()
            e={"kind":"RELATION","entity_id":"one","day":1,"scope":"PRIVATE_CHARACTER","line":1,"anchor":prose,"value":{"target_id":"two","relation":"CONFIDENCE","value":"secret"}}
            delta={"schema":SCHEMA,"episode":"fixture","prose_sha256":sha,"events":[e],"new_entities":[],"unresolved":[]}
            apply_delta(db,delta,prose,1,1,sha,set())
            self.assertEqual(events_for_entity(db,"two"),[])
            self.assertEqual(events_for_entity(db,"two",public=False)[0]["roles"],["TARGET"])
