"""R25 integration under additive R26 v3: legacy R25 receipts still required."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_git_cycle import OPTIONS, EVENT, KNOWLEDGE, META
from worldroot.git_cycle import canonical, load, sha
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release
from worldroot.ledger import GateError

NEW_ID = "SYNTHETIC-LVI-C05-PV-D563"
HEAD_ID = "LVI-C05-PIV-D562-AUTHOR-SOURCE"
PROSE = (
    "## I — Uma carta nas mãos\n"
    "DIA 563 · 08h00 · BOSQUE\n"
    "Uma personagem sintetica decide escrever uma carta por vontade propria.\n"
    "**LUCAS —** O que muda quando alguém decide partir?\n"
    "## II — O caminho\n"
    "DIA 563 · 11h00 · BOSQUE\n"
    "O caminho diante da cidade permaneceu aberto a todos.\n"
    "**MIREN —** Vamos ouvir antes de decidir.\n"
    "## III — A escolha alheia\n"
    "DIA 563 · 14h00 · BOSQUE\n"
    "A soberana levou a pergunta até os guardiões da aldeia.\n"
    "**ELEN —** Eu escolho continuar aqui.\n"
)
FULL = PROSE + "\n" + "\n".join(
    f"{item.number} — {item.title}\n{item.description}" for item in OPTIONS
)
REVIEW = {
    "schema": "worldroot-reader-review-v1",
    "decision": "REVISADO_COM_EVIDENCIAS",
    "scene_evidence": [
        {
            "scene": "I",
            "literal_anchor": "Uma personagem sintetica decide escrever uma carta por vontade propria.",
            "felt_experience": "Lucas escuta uma decisão que não lhe pertence.",
            "scene_turn": "A carta materializa uma decisão independente.",
            "lasting_consequence": "Alguém prepara uma nova viagem autônoma.",
        },
        {
            "scene": "II",
            "literal_anchor": "O caminho diante da cidade permaneceu aberto a todos.",
            "felt_experience": "Miren examina o caminho com liberdade.",
            "scene_turn": "O grupo abandona uma hipótese apressada.",
            "lasting_consequence": "Os moradores escolhem como seguir juntos.",
        },
    ],
}
DIRECTION = {
    "schema": "worldroot-narrative-direction-v1",
    "source_episode_id": HEAD_ID,
    "author_choice": "Lucas escolheu caminhar pelo bosque junto de Miren.",
    "reader_promise": "Viver decisões independentes e escutar uma nova comunidade.",
    "lucas_lived_focus": "Lucas percebe, reage e conversa com diferentes pessoas.",
    "central_change": "O conselho abre um novo caminho para os moradores.",
    "independent_world": ["Elyrien e os guardiões seguem caminhos próprios."],
    "unknowns_preserved": ["Talis continua não localizada"],
    "does_not_choose_for_lucas": True,
}


class R25ArchiveIntegrationTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        h = self.root / "canon" / "HEAD.json"
        h.parent.mkdir()
        h.write_bytes(canonical({
            "schema": "worldroot-git-canon-v1",
            "episode_id": HEAD_ID, "day": 562,
            "book": "Livro VI", "chapter": 5,
            "part": "IV", "hour": "22h16",
        }))
        event = {
            **EVENT,
            "source": {
                "sha256": sha(FULL.encode("utf-8")),
                "line": 3,
                "literal_anchor": "Uma personagem sintetica decide escrever uma carta",
            },
        }
        self.payload = {
            "schema": "worldroot-draft-inbox-v3",
            "delivery_id": NEW_ID,
            "prose": PROSE,
            "full_text": FULL,
            "metadata": {
                **META, "day": 563, "book": "Livro VI",
                "chapter": 5, "part": "V", "hour": "22h43",
            },
            "choices": [vars(x) for x in OPTIONS],
            "book_closed": False,
            "editorial_visibility": "PRIVADO",
            "reviewed_events": [event],
            "reviewed_knowledge": [{**KNOWLEDGE, "acquired_day": 563}],
            "narrative_direction": DIRECTION,
            "reader_review": REVIEW,
            "fantasy_review": {
                "schema": "worldroot-r26-fantasy-review-v1",
                "source_episode_id": HEAD_ID,
                "cannot_choose_for_author": True,
                "genese_unrestricted": True,
                "backstage_invisible": True,
                "spell_uses": [], "summon_uses": [],
                "combat": {"mode": "SEM_COMBATE"},
                "wonder": {"mode": "SEM_DESCOBERTA"},
                "moments": [],
                "character_evolution": [{
                    "name": "LUCAS",
                    "literal_anchor": "Uma personagem sintetica decide escrever uma carta por vontade propria.",
                    "decision_or_reaction": "Lucas permite a decisão independente e escuta a personagem.",
                    "emotional_or_relational_delta": "O vínculo entre os personagens permanece em liberdade.",
                    "new_power_claimed": False,
                }],
                "variation_decision": "A sequência acompanha três cenas conectadas e não comprime uma batalha artificial.",
            },
        }
        self.inbox = self.root / "inbox" / (NEW_ID + ".json")
        self.write()

    def write(self):
        self.inbox.parent.mkdir(exist_ok=True)
        self.inbox.write_bytes(canonical(self.payload))

    def run_archive(self):
        with patch("worldroot.draft_inbox.presentation_preflight",
                   return_value={"errors": [], "status": "OK"}):
            return archive_inbox(self.root, self.inbox)

    def test_r25_creates_readback_evidence_and_legacy_canon_unchanged(self):
        result = self.run_archive()
        self.assertEqual(result["status"], "RASCUNHO_GITHUB_VERIFICADO")
        self.assertEqual(result["changed_file_count"], 10)
        self.assertTrue((self.root / "episodes" / NEW_ID /
                         "review" / "experiencia_r25.json").is_file())
        self.assertEqual(load(self.root / "canon" / "HEAD.json")["episode_id"], HEAD_ID)
        with patch("worldroot.delivery_gate.presentation_preflight",
                   return_value={"errors": [], "status": "OK"}):
            delivered = audit_release(self.root, NEW_ID)
        self.assertTrue(delivered["release_allowed"], delivered)
        self.assertEqual(delivered["r25_contract"], "ENFORCED")
        self.assertTrue(delivered["checks"]["r25_reader_evidence"])

    def test_draft_must_have_source_anchored_editorial_evidence(self):
        self.payload["reader_review"] = {
            **REVIEW,
            "scene_evidence": [
                {**REVIEW["scene_evidence"][0], "literal_anchor": "never happened"},
                REVIEW["scene_evidence"][1],
            ],
        }
        self.write()
        with self.assertRaises(GateError):
            self.run_archive()
        self.assertFalse((self.root / "episodes" / NEW_ID).exists())

    def test_old_v1_contract_cannot_open_new_livro_vi(self):
        self.payload["schema"] = "worldroot-draft-inbox-v1"
        self.payload.pop("reader_review")
        self.payload.pop("narrative_direction")
        self.write()
        with self.assertRaisesRegex(GateError, "R26"):
            self.run_archive()
        self.assertFalse((self.root / "episodes" / NEW_ID).exists())

    def test_existing_r25_archive_is_idempotent_after_head_advances(self):
        self.run_archive()
        head_path = self.root / "canon" / "HEAD.json"
        head = load(head_path)
        head.update({"episode_id": NEW_ID, "day": 563, "part": "V", "hour": "22h43"})
        head_path.write_bytes(canonical(head))
        receipt = self.run_archive()
        self.assertEqual(receipt["changed_file_count"], 0)


if __name__ == "__main__":
    unittest.main()
