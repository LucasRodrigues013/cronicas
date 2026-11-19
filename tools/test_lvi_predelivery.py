"""Synthetic pre-delivery source recovery checks, without private real story."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from lvi_predelivery import prepare_lvi, canonical, ArchiveInvalid
from verify_lvi_original import verify_lvi


class LviPreDeliveryTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.id = "LVI-C02-PIV-D540-AUTHOR-SOURCE"
        self.episode = self.root / "episodes" / self.id
        draft = self.episode / "draft"
        review = self.episode / "review"
        draft.mkdir(parents=True)
        review.mkdir()
        (self.root / "inbox").mkdir()
        (self.root / "editorial/rejections").mkdir(parents=True)
        self.prose = "Teste de capítulo futuro da cidade livre, verificável por texto e hash.\n"
        self.choices = [{"number": n, "title": "Escolha " + str(n),
                         "is_special": n == 4, "is_free": n == 5} for n in range(1, 6)]
        self.full = self.prose + "\n".join(x["title"] for x in self.choices) + "\n"
        metadata = {"book": "Livro VI", "chapter": 2, "part": "IV", "day": 540,
                    "hour": "11h21", "location": "Três Arcos", "canon_status": "RASCUNHO"}
        payload = {
            "schema": "worldroot-draft-inbox-v1",
            "delivery_id": self.id, "full_text": self.full,
            "character_preflight": [{
                "name": "Lucas",
                "last_physical_appearance_source": "Última cena canônica auditada",
                "location_at_scene": "Três Arcos",
                "affiliation_at_scene": "Fundador livre",
                "knowledge_at_scene": "Apenas evidências recebidas",
            }],
        }
        (self.root / "inbox" / (self.id + ".json")).write_bytes(canonical(payload))
        structured = {
            "delivery_id": self.id, "full_text": self.full, "prose": self.prose,
            "metadata": metadata, "choices": self.choices, "events": [],
            "book_closed": False, "editorial_visibility": "PRIVADO",
        }
        components = {
            "narrativa_integral.md": self.full.encode("utf-8"),
            "opcoes.json": canonical(self.choices),
            "eventos_e_consequencias.json": canonical([]),
            "checkpoint_candidato.json": canonical(metadata),
            "episode_draft.json": canonical(structured),
        }
        for path, body in components.items():
            (draft / path).write_bytes(body)
        source_sha = hashlib.sha256(self.full.encode()).hexdigest()
        manifest = {
            "schema": "worldroot-episode-package-v1",
            "delivery_id": self.id, "canon_status": "RASCUNHO",
            "original_readback_sha256": source_sha,
            "artifacts": {
                k: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
                for k,b in components.items()
            },
        }
        (draft / "manifesto_imutavel.json").write_bytes(canonical(manifest))
        events = {
            "episode_id": self.id,
            "review_status": "REVISADO",
            "source_sha256": source_sha,
            "events": [{
                "event_id": "TEST-001",
                "source": {"line": 1, "literal_anchor": "Teste de capítulo futuro",
                           "sha256": source_sha},
            }],
        }
        (review / "eventos_revisados.json").write_bytes(canonical(events))

    def test_predelivery_exact_source_and_reviews(self):
        result = prepare_lvi(self.root, self.id)
        self.assertEqual(result["status"], "PREDELIVERY_SOURCE_ARCHIVED_SHA_VERIFIED")
        self.assertEqual(result["ui_parity"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(prepare_lvi(self.root, self.id), result)
        self.assertEqual(verify_lvi(self.root, self.id)["result"], "ORIGINAL_MATCHED_ARCHIVE_REVIEWED")

    def test_character_matrix_missing_blocks_before_proof(self):
        path = self.root / "inbox" / (self.id + ".json")
        payload = json.loads(path.read_text())
        del payload["character_preflight"]
        path.write_bytes(canonical(payload))
        with self.assertRaisesRegex(ArchiveInvalid, "character_preflight"):
            prepare_lvi(self.root, self.id)
        self.assertFalse((self.root / "editorial/recovery/originals").exists())

    def test_source_change_rejected(self):
        path = self.root / "inbox" / (self.id + ".json")
        payload = json.loads(path.read_text())
        payload["full_text"] += "alterado"
        path.write_bytes(canonical(payload))
        with self.assertRaisesRegex(ArchiveInvalid, "differs"):
            prepare_lvi(self.root, self.id)

    def test_review_anchor_tamper_blocks(self):
        p = self.episode / "review/eventos_revisados.json"
        payload = json.loads(p.read_text())
        payload["events"][0]["source"]["line"] = 2
        p.write_bytes(canonical(payload))
        with self.assertRaisesRegex(ArchiveInvalid, "not anchored"):
            prepare_lvi(self.root, self.id)

    def test_source_proof_fails_on_mutation(self):
        prepare_lvi(self.root, self.id)
        path = self.root / "editorial/recovery/originals" / (self.id + ".txt")
        path.write_text("alterado", encoding="utf-8")
        with self.assertRaisesRegex(ArchiveInvalid, "conflict"):
            prepare_lvi(self.root, self.id)


if __name__ == "__main__":
    unittest.main()
