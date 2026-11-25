import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot.living_world import advisory, resolve_entities, project, receipt, SEED, literal_body

class LivingWorldTests(unittest.TestCase):
    def test_alias_collision_not_merged(self):
        r=resolve_entities({"entities":[{"id":"institute","name":"AERÚN Instituto","aliases":["AERUN"]},
             {"id":"dragon","name":"AERÚN Guardião","aliases":["AERÚN"]}]})
        self.assertEqual(r["ambiguous"]["aerun"],["dragon","institute"])
        self.assertNotIn("aerun",r["aliases"])

    def test_compression_and_checkpoints(self):
        draft="\n".join(f"## {n} — Cena\nLucas falou. magia." for n in ["I","II","III","IV","V"])
        long=draft.replace("Lucas falou.","Lucas falou. "*100)
        out=advisory(draft+"\n**FIM DA PARTE I**\n"+"ruído "*500,[long])
        self.assertTrue(any(x.startswith("DEPTH:") for x in out["notices"]))
        self.assertEqual(out["depth"]["scene_count"],5)
        self.assertFalse(out["canon_changed"])
        self.assertNotIn("ruído",literal_body(draft+"\n**FIM DA PARTE I**\nruído"))

    def fixture(self,root):
        ident="LVI-C01-PI-D538"
        body="## I — Cena\n**LUCAS —** Olá.\nÉgide Interna construída."
        digest=hashlib.sha256(body.encode()).hexdigest()
        def put(p,obj):
            path=root/p;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
        head={"schema":"worldroot-git-canon-v1","sequence":1,"episode_id":ident,"day":538,"source_sha256":digest}
        put("canon/HEAD.json",head)
        put(f"canon/episodes/{ident}.json",{"schema":"worldroot-github-closure-v1","sequence":1,"episode_id":ident,
             "metadata":{"day":538},"story_sha256":digest})
        f=root/f"episodes/{ident}/draft/narrativa_integral.md";f.parent.mkdir(parents=True);f.write_text(body,encoding="utf-8")
        put(SEED,{"assets":[{"id":"shield","name":"Égide Interna","state":"CREATED","source":{"episode":ident,"anchor":"Égide Interna construída."}},
             {"id":"pending","name":"Último Horizonte","state":"DEFERRED","source":{"episode":ident,"anchor":"inexistente"}}],
             "entities":[{"id":"lucas","name":"Lucas","kind":"character"},{"id":"kairon","name":"Káiron","kind":"character"}],
             "plots":[{"id":"p","aliases":["Égide"],"source":{"episode":ident,"anchor":"Égide Interna construída."}}]})
        # A newer draft, not in canonical journal, must never enter the projection.
        d=root/"episodes/LVI-C01-PII-D539/draft";d.mkdir(parents=True);(d/"narrativa_integral.md").write_text("Káiron aparece")
        return head,f

    def test_source_projection_and_draft_exclusion(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);head,f=self.fixture(root)
            before=(root/"canon/HEAD.json").read_bytes()
            out=project(root)
            self.assertEqual(out["coverage"]["closed_episodes"],1)
            self.assertEqual(out["assets"][0]["evidence_status"],"SOURCE_MATCH")
            self.assertEqual(out["assets"][1]["evidence_status"],"UNVERIFIED")
            self.assertTrue(out["characters"][1]["requires_legacy_recovery"])
            self.assertEqual(out["characters"][0]["days_since_dialogue"],0)
            self.assertEqual((root/"canon/HEAD.json").read_bytes(),before)
            with self.assertRaises(ValueError): project(root,{**head,"day":539})
            f.write_text("tampered")
            self.assertEqual(project(root)["status"],"PARTIAL")
            self.assertEqual(project(root)["assets"][0]["evidence_status"],"UNVERIFIED")

    def test_receipt_advisory_no_seed_required(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);head,_=self.fixture(root)
            self.assertEqual(receipt("## I — Teste\nUma cena.",root,head)["status"],"ADVISORY_ONLY")

if __name__=="__main__": unittest.main()
