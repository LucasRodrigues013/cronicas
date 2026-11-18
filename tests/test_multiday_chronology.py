"""A lived chapter may cross days, but the archive may never infer missing dates."""
import unittest

from worldroot.git_cycle import _chronology
from worldroot.ledger import GateError

HEAD = {"book": "Livro V", "chapter": 16, "part": "III", "day": 534, "hour": "18h11"}
END = {"book": "Livro V", "chapter": 16, "part": "IV", "day": 537,
       "hour": "11h46", "location": "Campo Aurora"}
PROSE = """
## I — A noite da conversa
<text>DIA 534 · 20h08 · CASA DO JARDIM BRANCO</text>
Lucas e Miren conversam.

## II — A reunião e a noite
<text>DIA 535 · 09h16 · CAMPO AURORA</text>
A equipe planeja.

## III — A inspeção e o descanso
<text>DIA 536 · 19h03 · CAMPO AURORA</text>
A equipe descansa depois de trabalhar.

## IV — A decolagem e o retorno
<text>DIA 537 · 11h46 · CAMPO AURORA</text>
A missão volta.
"""


class MultiDayChronologyTest(unittest.TestCase):
    def test_narrated_four_day_part_passes(self):
        _chronology(HEAD, END, prose=PROSE)

    def test_no_scene_evidence_cannot_jump_three_days(self):
        with self.assertRaises(GateError):
            _chronology(HEAD, END)

    def test_missing_intermediate_day_is_blocked(self):
        with self.assertRaises(GateError):
            _chronology(HEAD, END, prose=PROSE.replace("DIA 536", "DIA 535"))

    def test_backwards_clock_is_blocked(self):
        with self.assertRaises(GateError):
            _chronology(HEAD, END, prose=PROSE.replace("DIA 536", "DIA 534"))

    def test_metadata_must_match_last_explicit_scene_clock(self):
        with self.assertRaises(GateError):
            _chronology(HEAD, {**END, "hour": "12h30"}, prose=PROSE)

    def test_single_day_next_day_remains_compatible(self):
        _chronology(HEAD, {**END, "day": 535, "hour": "06h00"})


if __name__ == "__main__":
    unittest.main()
