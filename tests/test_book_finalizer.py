"""Fail-closed author-approved final-book journal regression tests."""
import json
import tempfile
import unittest
from pathlib import Path

from worldroot.book_finalizer import author_finale_choice, finalize_book
from worldroot.ledger import GateError

PREV = "LV-C16-PIV-D537-AUTHOR-SOURCE"
NEXT = "LV-C16-PV-D537-AUTHOR-SOURCE"
MESSAGE = "Vamos finalizar o ultimo capitulo de forma glorisa, e encerrar o livro V. Faça o ultimo capitulo digno."

class BookFinalizerTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        c = self.root/"choices"/PREV/"option-5.json"
        c.parent.mkdir(parents=True)
        c.write_text(json.dumps({"schema":"worldroot-author-choice-v1",
            "episode_id":PREV,"option":5,"free_text":MESSAGE,
            "author_source":"USER_MESSAGE"}),encoding="utf-8")
        a = self.root/"author-approvals"/(NEXT+".json")
        a.parent.mkdir()
        a.write_text(json.dumps({"schema":"worldroot-author-book-end-v1",
            "episode_id":NEXT,"book":"Livro V","approved":True,
            "author_source":"USER_MESSAGE","author_quote":MESSAGE,
            "previous_episode_id":PREV,
            "choice_path":f"choices/{PREV}/option-5.json"}),encoding="utf-8")

    def test_finale_choice_is_not_phantom_post_finale_selection(self):
        c=author_finale_choice(self.root,NEXT)
        self.assertEqual(c["option"],0)
        self.assertEqual(c["episode_id"],NEXT)
        self.assertEqual(c["free_text"],MESSAGE)
        self.assertEqual(c["schema"],"worldroot-author-book-finalize-v1")

    def test_no_request_no_finalization(self):
        with self.assertRaises(GateError):
            finalize_book(self.root)

    def test_request_unmatched_previous_episode_is_blocked(self):
        req=self.root/"canon"/"BOOK_END_REQUEST.json"
        req.parent.mkdir()
        req.write_text(json.dumps({"schema":"worldroot-book-end-request-v1",
            "episode_id":NEXT,"previous_episode_id":"INVALID",
            "book":"Livro V","author_source":"USER_MESSAGE",
            "approval_path":"author-approvals/"+NEXT+".json"}),encoding="utf-8")
        with self.assertRaises(GateError):
            finalize_book(self.root)


if __name__=="__main__":
    unittest.main()
