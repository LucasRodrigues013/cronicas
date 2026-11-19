"""New-book boundary refuses implicit continuity; author controls Livro VI."""
import json
import tempfile
import unittest
from pathlib import Path

from worldroot.book_opening import require_book_open_approval
from worldroot.git_cycle import _chronology
from worldroot.ledger import GateError

QUOTE = ("Quero que grave aquilo que gosto, Lucas bem expressivo, creation e gênese sem "
         "limites, miren e Lucas em uma relacionamento que se desenvolve. "
         "Autorizo iniciar Livro VI")
END = {"schema":"worldroot-git-canon-v1","book":"Livro V","book_closed":True,
       "chapter":16,"part":"V","episode_id":"LV-C16-PV-D537-AUTHOR-SOURCE",
       "sequence":9,"day":537,"hour":"23h46","source_sha256":"a"*64}
BEGIN = {"book":"Livro VI","chapter":1,"part":"I","day":538,
         "hour":"09h12","location":"Três Arcos"}

class BookOpeningTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        p=self.root/"author-approvals"/"LVI-OPEN.json"
        p.parent.mkdir()
        self.path=p
        self.approval={
            "schema":"worldroot-author-book-open-v1",
            "project":"CRONICAS_DE_UM_NOVO_MUNDO",
            "approved":True,"author_source":"USER_MESSAGE",
            "previous_book":"Livro V","next_book":"Livro VI",
            "previous_episode_id":END["episode_id"],
            "previous_sequence":END["sequence"],
            "previous_head_source_sha256":END["source_sha256"],
            "author_quote":QUOTE,
            "new_book_canon_head_written":False}
        self.save()
    def save(self):
        self.path.write_text(json.dumps(self.approval),encoding="utf-8")

    def test_author_approval_precedes_new_book(self):
        grant=require_book_open_approval(self.root,END,BEGIN)
        self.assertEqual(grant["status"],"AUTHOR_APPROVED_BOOK_VI_DRAFT_ONLY")
        self.assertFalse(grant["canon_changed"])
        self.assertFalse(grant["choice_recorded"])
        _chronology(END,BEGIN,book_open_approval_verified=True)
    def test_new_explicit_user_20261119_phrase_is_accepted_without_reinventing_quote(self):
        self.approval["author_quote"] = (
            "WORLDROOT — INICIAR LIVRO VI\\n"
            "CRÔNICAS DE UM NOVO MUNDO\\n"
            "ESTA É MINHA NOVA AUTORIZAÇÃO EXPLÍCITA PARA INICIAR A HISTÓRIA."
        ).replace("\\\\n", "\\n")
        self.save()
        grant = require_book_open_approval(self.root, END, BEGIN)
        self.assertEqual(grant["status"], "AUTHOR_APPROVED_BOOK_VI_DRAFT_ONLY")

    def test_generic_start_without_book_vi_identity_stays_blocked(self):
        self.approval["author_quote"] = "ESTA É MINHA NOVA AUTORIZAÇÃO EXPLÍCITA PARA INICIAR A HISTÓRIA."
        self.save()
        with self.assertRaises(GateError):
            require_book_open_approval(self.root, END, BEGIN)

    def test_without_verified_approval_new_book_stays_blocked(self):
        with self.assertRaises(GateError):
            _chronology(END,BEGIN)
    def test_no_unapproved_future_book_or_chapter(self):
        for meta in (dict(BEGIN, book="Livro VII"),
                     dict(BEGIN,part="II"),
                     dict(BEGIN, chapter=2),
                     dict(BEGIN,day=536)):
            with self.subTest(meta=meta):
                with self.assertRaises(GateError):
                    require_book_open_approval(self.root,END,meta)
    def test_prior_author_opening_revoked_in_preproduction(self):
        self.approval["approved"] = False
        self.approval["book_vi_opening_status"] = "AUTHOR_CLARIFIED_PLANNING_ONLY_PREMATURE_APPROVAL_REVOKED"
        self.save()
        with self.assertRaises(GateError):
            require_book_open_approval(self.root, END, BEGIN)

    def test_book_vi_one_day_per_part_no_day_skips(self):
        with self.assertRaises(GateError):
            _chronology(END, dict(BEGIN, day=539), book_open_approval_verified=True)
        p = "## I — chegada\nDIA 538 · 07h00 · ponte\nCena.\n## II — depois\nDIA 539 · 08h00 · vila\nFim."
        with self.assertRaises(GateError):
            _chronology(END, dict(BEGIN, day=538), prose=p, book_open_approval_verified=True)
        p = "## I — chegada\nDIA 538 · 07h00 · ponte\nCena.\n## II — conversa\nDIA 538 · 08h00 · vila\nFim."
        _chronology(END, dict(BEGIN, day=538), prose=p, book_open_approval_verified=True)

    def test_opening_cannot_be_forged_from_unquoted_story(self):
        self.approval["author_quote"]="I would love to start someday."
        self.save()
        with self.assertRaises(GateError):
            require_book_open_approval(self.root,END,BEGIN)
    def test_head_movement_blocks_recorded_approval(self):
        head=dict(END,sequence=10)
        with self.assertRaises(GateError):
            require_book_open_approval(self.root,head,BEGIN)
    def test_unclosed_previous_book_blocks_author_bridge(self):
        head=dict(END,book_closed=False)
        with self.assertRaises(GateError):
            require_book_open_approval(self.root,head,BEGIN)
    def test_same_day_cannot_go_backwards(self):
        m=dict(BEGIN,day=537,hour="22h30")
        with self.assertRaises(GateError):
            _chronology(END,m,book_open_approval_verified=True)
    def test_day538_narrates_no_artificial_intermediate_days(self):
        _chronology(END,BEGIN,book_open_approval_verified=True)

if __name__=="__main__":
    unittest.main()
