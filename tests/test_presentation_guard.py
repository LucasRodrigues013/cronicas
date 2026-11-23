"""Presentation regression: approve rich structure, catch loss of design."""
import unittest

from worldroot.presentation_guard import load_presentation_policy, presentation_preflight

RICH = """<box align="center">
<text>CRÔNICAS DE UM NOVO MUNDO · WORLDROOT</text>
<title>LIVRO V — ALÉM DAS ÚLTIMAS ESTRADAS</title>
<title>CAPÍTULO 15 · PARTE IV DE V</title>
<title>A CIDADE QUE APRENDEU A SONHAR</title>
</box>
<box border radius="lg">
<text>CALENDÁRIO DO HORIZONTE</text>
<grid columns={2}><grid-item>DIA 529 · ANO II · MÊS 06 · DIA 14</grid-item></grid>
</box>
## I — A porta
DIA 529 · 22h02 · TRÊS ARCOS
**LUCAS —** Bom dia.
**MIREN —** Boa noite.
## II — A promessa
DIA 529 · 22h43 · TRÊS ARCOS
**VARO —** Entendi.
**KÁIRON —** Concordo.
## III — A escolha
DIA 529 · 23h12 · TRÊS ARCOS
**SISTEMA —** Ainda é cedo.
<box border radius="lg">
<text>WORLDROOT · CHECKPOINT NARRATIVO</text>
<grid columns={2}><grid-item>Dia 529</grid-item></grid>
</box>
## ESCOLHAS DE CONTINUIDADE
<box><button onClick={()=>GenUI.issueNewTurn("Opção 1")}>1</button>
<button onClick={()=>GenUI.issueNewTurn("Opção 2")}>2</button>
<button onClick={()=>GenUI.issueNewTurn("Opção 3")}>3</button>
<text>4 — ESPECIAL</text>
<button onClick={()=>GenUI.issueNewTurn("Opção 4")}>4</button>
<text>5 — AÇÃO LIVRE</text>
<textarea value={texto} onChange={setTexto}/>
<button disabled={!texto.trim()} onClick={()=>GenUI.issueNewTurn(texto)}>Enviar</button></box>
"""
FLAT = """# CRÔNICAS DE UM NOVO MUNDO
**LIVRO V — ALÉM DAS ÚLTIMAS ESTRADAS**
**CAPÍTULO 15 · PARTE III DE V**
# A NOITE EM QUE NINGUÉM FICOU PARA TRÁS
**CALENDÁRIO DO HORIZONTE — DIA 529 · ANO II · MÊS 06 · DIA 14**
## I — Primeiro ato
**LUCAS —** Oi.
## II — Segundo ato
**MIREN —** Olá.
## III — Terceiro ato
**VARO —** Vamos.
## ESCOLHAS
1 — Algo. 2 — Outro. 3 — Mais. 4 — ESPECIAL. 5 — AÇÃO LIVRE.
"""

class PresentationContractTest(unittest.TestCase):
    def test_policy_is_classified_and_project_scoped(self):
        p = load_presentation_policy()
        self.assertEqual(p["version"], 2)
        self.assertEqual(len(p["classifications"]), 12)
        self.assertEqual(p["project"], "CRONICAS_DE_UM_NOVO_MUNDO")

    def test_rich_story_layout_is_accepted(self):
        result = presentation_preflight(RICH)
        self.assertEqual(result["status"], "OK", result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertFalse(result["screenshot_certification"])

    def test_markdown_only_regression_is_blocked(self):
        result = presentation_preflight(FLAT)
        self.assertEqual(result["status"], "BLOQUEADO")
        self.assertIn("rich_header", " ".join(result["errors"]))
        self.assertIn("choice_controls", " ".join(result["errors"]))

    def test_missing_checkpoint_is_blocked(self):
        result = presentation_preflight(
            RICH.replace("WORLDROOT · CHECKPOINT NARRATIVO", "INFORMAÇÕES"))
        self.assertEqual(result["status"], "BLOQUEADO")

    def test_fake_interactions_are_blocked(self):
        result = presentation_preflight(
            RICH.replace("GenUI.issueNewTurn", "GenUI.fakeAction"))
        self.assertEqual(result["status"], "BLOQUEADO")
        self.assertFalse(result["checks"]["choice_controls"])

    def test_cannot_claim_semantic_or_visual_certification(self):
        result = presentation_preflight(RICH)
        self.assertIs(result["semantic_certification"], False)
        self.assertIs(result["screenshot_certification"], False)
        self.assertIs(result["canon_changed"], False)

if __name__ == "__main__":
    unittest.main()
