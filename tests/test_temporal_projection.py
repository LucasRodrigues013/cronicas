"""Synthetic regression: midnight events, knowledge and guarded replay overrides."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worldroot.git_cycle import apply_closure_db, clean_db
from worldroot.ledger import GateError
from worldroot.temporal_projection import (
    event_day, load_corrections, projected_knowledge_day,
)


class TemporalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "event_id": "SYNTHETIC-E01", "occurred_day": 529, "clock": "23h44",
            "summary_candidato": "A cena ocorre antes da virada do dia.",
            "event_type": "SCENE", "visibility": "PRIVADO_PERSONAGEM",
            "source": {"line": 17, "literal_anchor": "A cena sintetica antecede o novo dia."},
        }
        self.knowledge = {
            "person": "Personagem A", "source_event": "SYNTHETIC-E01",
            "knowledge": "Testemunhou a cena no dia anterior ao checkpoint",
            "acquired_day": 530, "clock": None, "visibility": "PRIVADO_PERSONAGEM",
        }
        self.correction = {
            "episode_id": "SYNTHETIC-EPISODE",
            "person": "Personagem A", "source_event": "SYNTHETIC-E01",
            "recorded_acquired_day": 530, "corrected_acquired_day": 529,
            "source_event_day": 529, "source_line": 17,
            "literal_anchor": "A cena sintetica antecede o novo dia.",
            "reason": "A testemunha estava presente na cena do dia 529, confirmada pelo texto integral.",
        }
        self.key = ("SYNTHETIC-EPISODE", "Personagem A", "SYNTHETIC-E01")

    def test_event_day_is_not_chapter_checkpoint_day(self):
        self.assertEqual(event_day(self.event, 530), 529)
        self.assertEqual(event_day({"event_id": "old-format"}, 530), 530)

    def test_future_source_event_day_is_blocked(self):
        with self.assertRaises(GateError):
            event_day({**self.event, "occurred_day": 531}, 530)
        with self.assertRaises(GateError):
            event_day({**self.event, "occurred_day": True}, 530)

    def test_correction_is_evidence_bound(self):
        self.assertEqual(
            projected_knowledge_day(self.key[0], self.knowledge, self.event,
                                    530, {self.key: self.correction}),
            529)
        altered = {**self.event, "source": {**self.event["source"],
                                           "literal_anchor": "Alteracao de fonte"}}
        with self.assertRaises(GateError):
            projected_knowledge_day(self.key[0], self.knowledge, altered,
                                    530, {self.key: self.correction})

    def test_no_override_does_not_infer_when_learned(self):
        self.assertEqual(
            projected_knowledge_day(self.key[0], self.knowledge, self.event,
                                    530, {}), 530)
        with self.assertRaises(GateError):
            projected_knowledge_day(
                self.key[0], {**self.knowledge, "acquired_day": 528},
                self.event, 530, {})

    def test_registry_is_versioned_and_refuses_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "canon"
            directory.mkdir()
            path = directory / "temporal-reconciliation.json"
            payload = {"schema": "worldroot-temporal-reconciliation-v1",
                       "scope": "PROJECTION_ONLY_NO_CANON_REWRITE",
                       "corrections": [self.correction]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(len(load_corrections(root, lambda p: json.loads(p.read_text()))), 1)
            payload["corrections"].append(self.correction)
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(GateError):
                load_corrections(root, lambda p: json.loads(p.read_text()))

    def test_projection_corrects_day_without_mutating_source_closure(self):
        closure = {
            "episode_id": "SYNTHETIC-EPISODE", "sequence": 1,
            "story_sha256": "story", "choice_sha256": "choice",
            "chosen_option": 4,
            "metadata": {"day": 530, "hour": "18h45", "chapter": 15,
                         "part": "III"},
            "events": [self.event], "knowledge": [self.knowledge],
        }
        before = json.dumps(closure, sort_keys=True)
        head = {"sequence": 1, "episode_id": "SYNTHETIC-EPISODE",
                "day": 530, "book": "Livro V", "chapter": 15, "part": "III",
                "hour": "18h45"}
        with sqlite3.connect(":memory:") as connection:
            clean_db(connection)
            apply_closure_db(connection, closure, head, {self.key: self.correction})
            self.assertEqual(connection.execute(
                "SELECT day FROM events WHERE event_id='SYNTHETIC-E01'").fetchone()[0], 529)
            self.assertEqual(connection.execute(
                "SELECT acquired_day FROM npc_knowledge").fetchone()[0], 529)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(json.dumps(closure, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
