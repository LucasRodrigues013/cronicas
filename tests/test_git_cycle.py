"""Offline regression of GitHub-only SQLite cycle; all names and text synthetic."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worldroot.episode_pipeline import EpisodeDraft
from worldroot.git_cycle import bootstrap, close, restore, verify_db, load, sha, canonical
from worldroot.ledger import GateError, ConflictError
from worldroot.choice_intake import IntakeError
from worldroot.narrative import Choice


OPTIONS = [
    Choice(1, "SYNTHETIC PATH ONE", "Choice text"),
    Choice(2, "SYNTHETIC PATH TWO", "Choice text"),
    Choice(3, "SYNTHETIC PATH THREE", "Choice text"),
    Choice(4, "SPECIAL SYNTHETIC PATH", "Choice text", is_special=True),
    Choice(5, "FREE SYNTHETIC PATH", "", is_free=True),
]
PROSE = ("LIVRO TESTE CAPITULO 15 PARTE II\n"
         "O teste precisa preservar a autonomia das personagens e o relogio.\n"
         "Uma personagem sintetica decide escrever uma carta por vontade propria.\n")
FULL = PROSE + "\n" + "\n".join(
    f"{x.number} — {x.title}\n{x.description}" for x in OPTIONS
)
META = {"day": 529, "book": "Livro V", "chapter": 15, "part": "II",
        "hour": "20h42", "location": "Cidade Sintetica", "choice": "4",
        "canon_status": "RASCUNHO"}
EVENT = {
    "event_id": "SYNTHETIC-EVENT-529-01",
    "event_type": "FAMILY",
    "summary_candidato": "Uma personagem sintetica escreveu uma carta por vontade propria.",
    "canon_status": "NARRADO", "visibility": "PRIVADO_PERSONAGEM",
    "clock": "11h00",
    "source": {"sha256": sha(FULL.encode("utf-8")), "line": 3,
               "literal_anchor": "Uma personagem sintetica decide escrever uma carta"},
}
KNOWLEDGE = {
    "person": "Personagem Sintetico",
    "source_event": EVENT["event_id"],
    "knowledge": "A carta foi escrita por vontade propria",
    "acquired_day": 529, "clock": "11h00", "visibility": "PRIVADO_PERSONAGEM",
}
ID = "SYNTHETIC-EPISODE-529"


def put(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(obj))


class GitCycleTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        base = self.root / "episodes" / "bootstrap" / "LV-C15-PI-D528"
        base.mkdir(parents=True)
        source = "Texto sintetico D528, nao e narrativa do usuario.\n".encode("utf-8")
        (base / "fonte_literal_drive_D528.txt").write_bytes(source)
        put(base / "manifesto_recuperacao.json", {
            "schema": "worldroot-bootstrap-source-v1",
            "status": "PRESERVED_HISTORICAL_LITERAL_ONLY",
            "utf8_bytes": len(source),
        })
        put(self.root / "canon" / "BOOTSTRAP_REQUEST.json", {
            "schema": "worldroot-bootstrap-request-v1",
            "source_episode": "LV-C15-PI-D528", "authorized_by": "USER_REQUEST",
            "source_sha256": sha(source),
        })
        self.draft = EpisodeDraft(ID, PROSE, FULL, META, OPTIONS, [])
        files = {
            "narrativa_integral.md": FULL.encode("utf-8"),
            "opcoes.json": canonical([vars(x) for x in OPTIONS]),
            "eventos_e_consequencias.json": canonical([]),
            "checkpoint_candidato.json": canonical(META),
            "episode_draft.json": canonical({
                "delivery_id": ID, "prose": PROSE, "full_text": FULL,
                "metadata": META, "choices": [vars(x) for x in OPTIONS],
                "events": [], "book_closed": False, "editorial_visibility": "PRIVADO",
            }),
        }
        draft = self.root / "episodes" / ID / "draft"
        draft.mkdir(parents=True)
        for name, content in files.items():
            (draft / name).write_bytes(content)
        put(draft / "manifesto_imutavel.json", {
            "schema": "worldroot-episode-package-v1", "delivery_id": ID,
            "canon_status": "RASCUNHO", "original_readback_sha256": sha(files["narrativa_integral.md"]),
            "artifacts": {k: {"sha256": sha(v), "bytes": len(v)} for k, v in files.items()},
        })
        self.choice = self.root / "choices" / ID / "option-4.json"
        put(self.choice, {"schema": "worldroot-author-choice-v1", "episode_id": ID,
                          "option": 4, "free_text": "", "author_source": "USER_MESSAGE"})
        self.events = self.root / "episodes" / ID / "review" / "eventos_revisados.json"
        self.knowledge = self.root / "episodes" / ID / "review" / "conhecimento_revisado.json"
        put(self.events, {
            "schema": "worldroot-reviewed-events-v1", "episode_id": ID,
            "review_status": "REVISADO", "source_sha256": sha(FULL.encode("utf-8")),
            "events": [EVENT],
        })
        put(self.knowledge, {
            "schema": "worldroot-reviewed-knowledge-v1", "episode_id": ID,
            "review_status": "REVISADO", "knowledge": [KNOWLEDGE],
        })

    def boot(self):
        return bootstrap(self.root)

    def test_bootstrap_does_not_promote_d529(self):
        result = self.boot()
        self.assertEqual(result["sequence"], 0)
        head = load(self.root / "canon" / "HEAD.json")
        self.assertEqual(head["day"], 528)
        self.assertEqual(verify_db(self.root, head)["episodes"], 0)

    def test_full_close_and_restore_without_oidc(self):
        self.boot()
        result = close(self.root)
        self.assertEqual(result["result"], "FECHADO_GITHUB")
        self.assertEqual((result["events"], result["knowledge"]), (1, 1))
        head = load(self.root / "canon" / "HEAD.json")
        self.assertEqual(head["day"], 529)
        db = self.root / "canon" / "state.sqlite"
        with sqlite3.connect(db) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM npc_knowledge").fetchone()[0], 1)
        db.unlink()
        self.assertEqual(restore(self.root)["episodes"], 1)
        verify_db(self.root, head)

    def test_duplicate_choice_is_idempotent(self):
        self.boot()
        close(self.root)
        again = close(self.root)
        self.assertEqual(again["result"], "IDEMPOTENTE")
        self.assertEqual(load(self.root / "canon" / "HEAD.json")["sequence"], 1)

    def test_no_review_means_no_change_to_head(self):
        self.boot()
        self.events.unlink()
        with self.assertRaises(GateError):
            close(self.root)
        self.assertEqual(load(self.root / "canon" / "HEAD.json")["day"], 528)

    def test_tampered_evidence_blocks(self):
        self.boot()
        event = dict(EVENT)
        event["source"] = {**EVENT["source"], "literal_anchor": "Fato que nao esta no texto"}
        data = load(self.events)
        data["events"] = [event]
        put(self.events, data)
        with self.assertRaises(GateError):
            close(self.root)
        self.assertFalse((self.root / "canon" / "episodes" / f"{ID}.json").exists())

    def test_knowledge_cannot_cite_unknown_event(self):
        self.boot()
        data = load(self.knowledge)
        data["knowledge"] = [{**KNOWLEDGE, "source_event": "NOT-NARRATED"}]
        put(self.knowledge, data)
        with self.assertRaises(GateError):
            close(self.root)

    def test_changed_selection_blocked(self):
        self.boot()
        data = load(self.choice)
        data["option"] = 3
        put(self.choice, data)
        with self.assertRaises(IntakeError):
            close(self.root)

    def test_missing_sqlite_is_fail_closed_then_recoverable(self):
        self.boot()
        (self.root / "canon" / "state.sqlite").unlink()
        with self.assertRaises(GateError):
            close(self.root)
        restore(self.root)
        self.assertEqual(close(self.root)["sequence"], 1)

    def test_unauthorized_future_book_transition_blocked(self):
        self.boot()
        data = load(self.events)
        self.draft = self.draft
        meta_path = self.root / "episodes" / ID / "draft" / "checkpoint_candidato.json"
        draft_path = self.root / "episodes" / ID / "draft" / "episode_draft.json"
        manifest_path = self.root / "episodes" / ID / "draft" / "manifesto_imutavel.json"
        meta = load(meta_path)
        meta["book"] = "Livro VI"
        put(meta_path, meta)
        draft_data = load(draft_path)
        draft_data["metadata"] = meta
        put(draft_path, draft_data)
        manifest = load(manifest_path)
        for p, name in ((meta_path, "checkpoint_candidato.json"), (draft_path, "episode_draft.json")):
            manifest["artifacts"][name] = {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
        put(manifest_path, manifest)
        with self.assertRaises(GateError):
            close(self.root)

    def test_bootstrap_twice_refused(self):
        self.boot()
        with self.assertRaises(GateError):
            self.boot()

    def test_duplicate_choice_paths_blocked(self):
        self.boot()
        put(self.choice.parent / "option-3.json", {
            "schema": "worldroot-author-choice-v1", "episode_id": ID,
            "option": 3, "free_text": "", "author_source": "USER_MESSAGE",
        })
        with self.assertRaises(IntakeError):
            close(self.root)


if __name__ == "__main__":
    unittest.main()
