"""Explicit user-linked approval is the only path to ending Livro V."""
import json
import tempfile
import unittest
from pathlib import Path
from worldroot.book_closure import require_book_end_approval
from worldroot.ledger import GateError

PREV = "LV-C16-PIV-D537-AUTHOR-SOURCE"
NEXT = "LV-C16-PV-D537-AUTHOR-SOURCE"
TEXT = "Vamos finalizar o ultimo capitulo de forma glorisa, e encerrar o livro V. Faça o ultimo capitulo digno."

class AuthorBookEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.choice = self.root/"choices"/PREV/"option-5.json"
        self.choice.parent.mkdir(parents=True)
        self.choice.write_text(json.dumps({
            "schema":"worldroot-author-choice-v1", "episode_id":PREV,
            "option":5, "free_text":TEXT, "author_source":"USER_MESSAGE"
        }), encoding="utf-8")
        self.approval = self.root/"author-approvals"/(NEXT+".json")
        self.approval.parent.mkdir(parents=True)
        self.data = {"schema":"worldroot-author-book-end-v1","episode_id":NEXT,
                     "book":"Livro V","approved":True,"author_source":"USER_MESSAGE",
                     "previous_episode_id":PREV,"choice_path":f"choices/{PREV}/option-5.json",
                     "author_quote":TEXT}
        self.approval.write_text(json.dumps(self.data),encoding="utf-8")

    def test_real_explicit_book_end_approval(self):
        r = require_book_end_approval(self.root,NEXT,"Livro V")
        self.assertEqual(r["status"],"EXPLICIT_AUTHOR_APPROVAL_VERIFIED")

    def test_no_approval(self):
        self.approval.unlink()
        with self.assertRaises(GateError):
            require_book_end_approval(self.root,NEXT,"Livro V")

    def test_wrong_quote_fails(self):
        self.data["author_quote"] = "FIM DO LIVRO V"
        self.approval.write_text(json.dumps(self.data),encoding="utf-8")
        with self.assertRaises(GateError):
            require_book_end_approval(self.root,NEXT,"Livro V")

    def test_model_approval_fails(self):
        self.data["author_source"] = "ASSISTANT"
        self.approval.write_text(json.dumps(self.data),encoding="utf-8")
        with self.assertRaises(GateError):
            require_book_end_approval(self.root,NEXT,"Livro V")

    def test_unrelated_book_fails(self):
        with self.assertRaises(GateError):
            require_book_end_approval(self.root,NEXT,"Livro IV")

    def test_previous_message_not_explicit_fails(self):
        obj=json.loads(self.choice.read_text())
        obj["free_text"]="Continue a aventura"
        self.choice.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaises(GateError):
            require_book_end_approval(self.root,NEXT,"Livro V")

if __name__ == "__main__":
    unittest.main()
