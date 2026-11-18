"""Regression: public CONTEXT must never contradict closed HEAD or leak meta cognition."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worldroot.git_cycle import write_context


def head(closed: bool, book="Livro V"):
    return {"schema": "worldroot-git-canon-v1", "sequence": 9,
            "episode_id": "C16-PV", "book": book, "book_closed": closed,
            "day": 537, "chapter": 16, "part": "V", "hour": "23h46"}


class ContextSemanticSafetyTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        folder = self.root / "canon"
        folder.mkdir()
        with sqlite3.connect(folder / "state.sqlite") as db:
            db.executescript("""
                CREATE TABLE events (
                  event_id TEXT, episode_id TEXT, summary TEXT,
                  event_type TEXT, visibility TEXT, day INTEGER, hour TEXT,
                  source_line INTEGER, source_anchor TEXT);
                CREATE TABLE npc_knowledge (
                  row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  person TEXT, event_id TEXT, episode_id TEXT,
                  description TEXT, acquired_day INTEGER, acquired_time TEXT,
                  visibility TEXT);
            """)
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
                       ("E01", "C16-PV", "Book V concluded", "BOOK_END",
                        "BASTIDORES", 537, "23h46", 30, "FIM DO LIVRO V"))
            db.execute("INSERT INTO npc_knowledge "
                       "(person,event_id,episode_id,description,acquired_day,visibility) "
                       "VALUES (?,?,?,?,?,?)",
                       ("Lucas", "E01", "C16-PV",
                        "I know I am a character whose book ended", 537, "BASTIDORES"))
            db.execute("INSERT INTO npc_knowledge "
                       "(person,event_id,episode_id,description,acquired_day,visibility) "
                       "VALUES (?,?,?,?,?,?)",
                       ("Lucas", "E01", "C16-PV",
                        "I remember a celebration as a lived experience", 537, "PRIVADO_PERSONAGEM"))

    def test_closed_book_is_not_mislabeled_open(self):
        result = write_context(self.root, head(True))
        notes = " ".join(result["prohibited_assumptions"])
        self.assertIn("Livro V is canonically CLOSED", notes)
        self.assertNotIn("remains OPEN", notes)
        self.assertEqual(result["head"]["book_closed"], True)
        self.assertEqual(result["editorial_only_knowledge_excluded"], 1)
        self.assertEqual(len(result["backstage_events_not_character_knowledge"]), 1)
        self.assertEqual(result["recent_narrated_events"], [])
        known = result["explicit_character_knowledge"]["Lucas"]
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0]["visibility"], "PRIVADO_PERSONAGEM")
        self.assertNotIn("whose book ended", json.dumps(known))

    def test_open_new_book_has_dynamic_message(self):
        result = write_context(self.root, head(False, book="Livro VI"))
        notes = " ".join(result["prohibited_assumptions"])
        self.assertIn("Livro VI remains OPEN", notes)
        self.assertNotIn("Livro V", notes)

    def test_readback_identical_to_file(self):
        result = write_context(self.root, head(True))
        actual = json.loads((self.root / "canon" / "CONTEXT.json").read_text())
        self.assertEqual(actual, result)

if __name__ == "__main__":
    unittest.main()
