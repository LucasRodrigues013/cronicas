"""One-time author-approved chronology exception; all other Livro VI parts stay strict."""
import unittest
from unittest.mock import patch

from worldroot.git_cycle import (
    _chronology, _is_exact_author_approved_c02_pv_exception,
    _C02_PV_MULTIDAY_APPROVED_PROSE_SHA256,
)
from worldroot.ledger import GateError

CLOCKS = [
    ("I", 546, "06h07", "one"), ("II", 546, "07h32", "two"),
    ("III", 546, "08h46", "three"), ("IV", 546, "09h23", "four"),
    ("V", 546, "11h08", "five"), ("VI", 546, "12h37", "six"),
    ("VII", 546, "10h11", "A forja onde o ferro começou a mentir"),
    ("VIII", 546, "11h56", "eight"), ("IX", 546, "14h38", "nine"),
    ("X", 546, "14h42", "ten"), ("XI", 546, "19h06", "eleven"),
    ("XII", 547, "06h26", "twelve"), ("XIII", 547, "07h41", "thirteen"),
    ("XIV", 547, "09h16", "fourteen"), ("XV", 547, "09h29", "fifteen"),
    ("XVI", 547, "11h08", "sixteen"), ("XVII", 547, "14h42", "seventeen"),
    ("XVIII", 547, "16h08", "eighteen"), ("XIX", 547, "18h33", "nineteen"),
    ("XX", 547, "21h04", "twenty"), ("XXI", 547, "21h38", "twenty one"),
    ("XXII", 548, "06h42", "twenty two"), ("XXIII", 548, "10h34", "twenty three"),
    ("XXIV", 548, "13h52", "twenty four"), ("XXV", 548, "16h19", "twenty five"),
    ("XXVI", 548, "19h28", "twenty six"), ("XXVII", 548, "22h31", "twenty seven"),
]


def synthetic_clocked_prose():
    chunks = []
    for roman, day, hour, title in CLOCKS:
        first = ("Mais cedo, o reino anão enfrenta a crise." if roman == "VII"
                 else "Os personagens fazem escolhas livres e reais.")
        location = ("REGIÃO ANÃ, VALE DOS OFÍCIOS BAIXOS" if roman == "VII"
                    else "MUNDO DE TESTE")
        chunks.append(f"## {roman} — {title}\n\n**DIA {day} · {hour} — {location}**\n\n{first}\n")
    return "\n".join(chunks)


class ScopedAuthorExceptionTest(unittest.TestCase):
    def setUp(self):
        self.previous = {
            "episode_id": "LVI-C02-PIV-D545-AUTHOR-SOURCE",
            "sequence": 18, "book": "Livro VI", "day": 545,
            "hour": "22h18", "chapter": 2, "part": "IV", "book_closed": False,
        }
        self.meta = {
            "book": "Livro VI", "chapter": 2, "part": "V",
            "day": 548, "hour": "22h31", "location": "Torre", "canon_status": "RASCUNHO",
        }

    def test_exact_signed_prose_exception_passes(self):
        with patch("worldroot.git_cycle.sha",
                   return_value=_C02_PV_MULTIDAY_APPROVED_PROSE_SHA256):
            self.assertTrue(_is_exact_author_approved_c02_pv_exception(
                self.previous, self.meta, synthetic_clocked_prose()))
            _chronology(self.previous, self.meta, prose=synthetic_clocked_prose())

    def test_wrong_hash_still_rejected(self):
        with self.assertRaisesRegex(GateError, "multi-day jump"):
            _chronology(self.previous, self.meta, prose=synthetic_clocked_prose())

    def test_wrong_previous_head_rejected_even_with_matching_hash(self):
        head = dict(self.previous, sequence=19)
        with patch("worldroot.git_cycle.sha",
                   return_value=_C02_PV_MULTIDAY_APPROVED_PROSE_SHA256):
            with self.assertRaisesRegex(GateError, "multi-day jump"):
                _chronology(head, self.meta, prose=synthetic_clocked_prose())

    def test_future_lvi_parts_still_single_day(self):
        head = dict(self.previous, day=548, hour="22h31", part="V", chapter=2,
                    episode_id="LVI-C02-PV-D546-D548-AUTHOR-SOURCE", sequence=19)
        meta = dict(self.meta, day=550, chapter=3, part="I", hour="10h00")
        with self.assertRaisesRegex(GateError, "multi-day jump"):
            _chronology(head, meta, prose="## I — Test\n\n**DIA 550 · 10h00 — PLACE**")

    def test_wrong_clock_structure_detected_after_hash_match(self):
        broken = synthetic_clocked_prose().replace(
            "## XXVII — twenty seven", "## XXVII — missing")
        broken = broken.replace("DIA 548 · 22h31", "DIA 548 · 22h30")
        with patch("worldroot.git_cycle.sha",
                   return_value=_C02_PV_MULTIDAY_APPROVED_PROSE_SHA256):
            with self.assertRaisesRegex(GateError, "clock contract"):
                _chronology(self.previous, self.meta, prose=broken)


if __name__ == "__main__":
    unittest.main()
