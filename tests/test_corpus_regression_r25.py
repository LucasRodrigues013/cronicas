"""R25 tests: corpus comparator never edits the source or certifies literature."""
import unittest
from worldroot.corpus_regression import compare


def part(n: int, named: bool) -> str:
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII",
             "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"]
    return "".join(
        "## " + roman[i] + " — História\n" +
        ("**LUCAS —** Vamos descobrir.\n" if named else "— Vamos descobrir.\n") +
        "O mundo vive enquanto o caminho muda.\n"
        for i in range(n)
    )


class CorpusRegressionR25(unittest.TestCase):
    def test_reports_archived_regression_pattern_without_retcon(self):
        reference = part(9, True)
        c04 = [part(18, True)] * 5
        c05 = [part(18, False)] * 5
        result = compare(reference, c04, c05)
        self.assertEqual(result["reference"]["dialogue_unlabeled"], 0)
        self.assertEqual(result["c05"][0]["dialogue_unlabeled"], 18)
        self.assertIn("R25_TEMPLATE", " ".join(result["c04"][2]["narrative_alerts"]))
        self.assertFalse(result["canon_changed"])
        self.assertFalse(result["literary_certification"])

    def test_incomplete_corpus_is_not_accepted(self):
        with self.assertRaises(ValueError):
            compare("## I — Exemplo\nUma cena.", ["x"] * 4, ["y"] * 5)


if __name__ == "__main__":
    unittest.main()
