"""Only evidence-verified, noncanonical transition context may be reused."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from worldroot.ledger import GateError
from worldroot.transition_baseline import inspect_transition_baseline, SCHEMA


class BookTransitionBaselineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.ep = "LV-C16-PV-D537-AUTHOR-SOURCE"
        self.story = "\n".join(f"Evidence line {i}: known past has consequences." for i in range(1, 7))
        self.digest = hashlib.sha256(self.story.encode()).hexdigest()
        path = self.root / "episodes" / self.ep / "draft"
        path.mkdir(parents=True)
        (path / "narrativa_integral.md").write_text(self.story, encoding="utf-8")
        journal = self.root / "canon" / "episodes"
        journal.mkdir(parents=True)
        (journal / (self.ep + ".json")).write_text(
            json.dumps({"status":"FECHADO_GITHUB", "story_sha256":self.digest}))
        self.head = {"episode_id":self.ep,"sequence":9,"source_sha256":self.digest,
                     "book_closed":True,"book":"Livro V"}
        (self.root / "canon" / "HEAD.json").write_text(json.dumps(self.head))
        self.claims = [{"id":f"ARC{i:02d}", "status":"ESTABELECIDO",
                        "episode_id":self.ep, "source_sha256":self.digest,
                        "literal_anchor":f"Evidence line {i}: known past",
                        "continuation_rule":"Do not rediscover the same learned lesson as if it were new."}
                       for i in range(1, 6)]
        self.baseline = {"schema":SCHEMA,"head_guard":dict(self.head),
                         "next_book":"Livro VI","claims":self.claims}

    def test_verified_source_prepares_but_does_not_open_next_book(self):
        report=inspect_transition_baseline(self.root,self.baseline)
        self.assertEqual(report["claims_verified"],5)
        self.assertEqual(report["next_book"],"Livro VI")
        self.assertFalse(report["next_book_started"])
        self.assertFalse(report["canon_changed"])
        self.assertFalse(report["semantic_quality_certified"])

    def test_forged_quote_is_rejected(self):
        self.claims[0]["literal_anchor"]="A new invented history line"
        with self.assertRaises(GateError):
            inspect_transition_baseline(self.root,self.baseline)

    def test_wrong_hash_is_rejected(self):
        self.claims[0]["source_sha256"]="0"*64
        with self.assertRaises(GateError):
            inspect_transition_baseline(self.root,self.baseline)

    def test_moved_head_fails_closed(self):
        self.head["sequence"]=10
        (self.root / "canon" / "HEAD.json").write_text(json.dumps(self.head))
        with self.assertRaises(GateError):
            inspect_transition_baseline(self.root,self.baseline)

    def test_unclosed_book_not_ready(self):
        self.head["book_closed"]=False
        self.baseline["head_guard"]["book_closed"]=False
        (self.root / "canon" / "HEAD.json").write_text(json.dumps(self.head))
        with self.assertRaises(GateError):
            inspect_transition_baseline(self.root,self.baseline)

    def test_backstage_book_is_not_a_character_memory(self):
        # Editorial truth can be source-verified but must not be presented as
        # in-world knowledge; this function does not certify that boundary.
        self.claims[0]["status"]="EDITORIAL"
        result=inspect_transition_baseline(self.root,self.baseline)
        self.assertFalse(result["character_knowledge_certified"])

if __name__ == "__main__":
    unittest.main()
