import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot.epic_narrative import DIRECTORS, SCHEMA, POLICY_FLAGS, review, validate_plan, _literal_evidence

class EpicNarrativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.ident="LVI-C01-PI-D538"
        self.prior="## I — Cena\nA promessa foi escrita na pedra."
        h=hashlib.sha256(self.prior.encode()).hexdigest()
        self.head={"episode_id":self.ident,"sequence":1,"source_sha256":h}
        f=self.root/"episodes"/self.ident/"draft/narrativa_integral.md"
        f.parent.mkdir(parents=True);f.write_text(self.prior,encoding="utf-8")
        c=self.root/"canon/episodes"/(self.ident+".json")
        c.parent.mkdir(parents=True);c.write_text(json.dumps({"schema":"worldroot-github-closure-v1",
            "episode_id":self.ident,"sequence":1,"story_sha256":h}),encoding="utf-8")
        self.source={"episode":self.ident,"anchor":"A promessa foi escrita na pedra."}
        self.prose="## I — Cena\nA maga encontrou um fragmento antigo e o levou à oficina."
        self.anchor="A maga encontrou um fragmento antigo e o levou à oficina."
    def card(self,kind):
        d={"director":kind,**{k:"Nota editorial de exemplo." for k in DIRECTORS[kind]},
           "draft_anchor":self.anchor,"prior_source":self.source}
        d.update(weakens_genese=False,outcome_open=True,fixed_deadline=None,
                 borrowed_protected_expression=False,omniscient=False)
        return d
    def packet(self,cards):
        return {"schema":SCHEMA,"source_episode_id":self.ident,"cards":cards,**{k:True for k in POLICY_FLAGS}}
    def test_all_ten_directors_evidence(self):
        out=review(self.prose,self.head,self.root,self.packet([self.card(k) for k in DIRECTORS]))
        self.assertEqual(out["card_status"],"ANCHORS_CHECKED")
        self.assertEqual(sum(v["anchored"] for v in out["directors"].values()),10)
        self.assertFalse(out["canon_changed"])
        self.assertFalse(out["literary_certification"])
    def test_no_quota_or_required_cards(self):
        out=review("Uma única cena tranquila.",self.head,self.root)
        self.assertEqual(out["card_status"],"NOT_SUPPLIED")
        self.assertEqual(out["notices"],[])
    def test_draft_and_tampered_prior_never_qualify(self):
        self.assertIsNotNone(_literal_evidence(self.root,self.head,self.source))
        self.assertIsNone(_literal_evidence(self.root,{**self.head,"sequence":0},self.source))
        self.assertIsNone(_literal_evidence(self.root,self.head,{"episode":"../other","anchor":self.anchor}))
        (self.root/"episodes"/self.ident/"draft/narrativa_integral.md").write_text("tampered")
        out=review(self.prose,self.head,self.root,self.packet([self.card("emotional_legacy")]))
        self.assertEqual(out["directors"]["emotional_legacy"]["anchored"],0)
    def test_stale_review_and_non_narrative_anchor(self):
        packet=self.packet([self.card("epic_moment")])
        packet["source_episode_id"]="old"
        self.assertEqual(review(self.prose,self.head,self.root,packet)["card_status"],"INVALID_OR_STALE")
        out=review("## I — Cena\nOutra coisa.\n**FIM DA PARTE I**\n"+self.anchor,
                   self.head,self.root,self.packet([self.card("epic_moment")]))
        self.assertEqual(out["directors"]["epic_moment"]["anchored"],0)
    def test_identity_flags_and_open_outcome(self):
        cards=[self.card("power_application"),self.card("long_arc"),self.card("originality"),self.card("antagonist_perspective")]
        cards[0]["weakens_genese"]=True
        cards[1]["fixed_deadline"]=580
        cards[2]["borrowed_protected_expression"]=True
        cards[3]["omniscient"]=True
        out=review(self.prose,self.head,self.root,self.packet(cards))
        self.assertEqual(sum(v["anchored"] for v in out["directors"].values()),0)
        self.assertEqual(len(out["notices"]),4)
    def test_plan_no_promotion(self):
        p={"schema":"worldroot-r29-creative-plan-v1","status":"AUTHOR_APPROVED_DIRECTION_NOT_CANON",
            "seeds":[{"id":"s","state":"POSSIBILITY_NOT_NARRATED","title":"T","premise":"P",
                       "entry_condition":"E","possible_reward":"R","safeguard":"S"}],
            "arcs":[{"id":"a","outcome_open":True,"fixed_deadline":None,"focus":"F"}]}
        self.assertEqual(validate_plan(p)["seed_count"],1)
        p["seeds"][0]["state"]="CANON"
        with self.assertRaises(ValueError): validate_plan(p)
        p["seeds"][0]["state"]="POSSIBILITY_NOT_NARRATED"
        p["arcs"][0]["fixed_deadline"]=580
        with self.assertRaises(ValueError): validate_plan(p)
if __name__=="__main__": unittest.main()
