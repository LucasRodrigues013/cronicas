"""Verifies imperial production scale without treating it as historical canon."""
import json
from pathlib import Path
import unittest


DATA = json.loads(
    (Path(__file__).resolve().parents[1] / "worldroot" / "bookvi_dominato_PROPOSAL.json")
    .read_text(encoding="utf-8")
)


class BookVIDominatoProposalTests(unittest.TestCase):
    def test_nine_provinces_plus_heartland_are_forty_two_million(self):
        self.assertEqual(DATA["status"], "PRECANON_HYPOTHETICAL_DONT_WRITE_HEAD")
        self.assertEqual(len(DATA["provinces"]), 9)
        self.assertTrue(all(p["confirmed_canon"] is False for p in DATA["provinces"]))
        self.assertEqual(round(sum(p["population_millions"] for p in DATA["provinces"]), 1), 32.4)
        self.assertEqual(round(DATA["vassal_population_millions"] + DATA["heartland_population_millions"], 1), 42.0)

    def test_active_reserve_force_no_double_count(self):
        self.assertEqual(sum(DATA["active_force"].values()), 260000)
        self.assertEqual(DATA["active_total"], 260000)
        self.assertEqual(DATA["reserve_militia"], 190000)
        self.assertEqual(DATA["paper_mobilization_total"], 450000)
        self.assertAlmostEqual(DATA["active_fraction_of_population"], 260000 / 42000000)

    def test_naval_crews_and_ships_are_consistent(self):
        self.assertEqual(sum(v["count"] for v in DATA["navy"].values()), 520)
        nominal = sum(v["count"] * v["crew_each"] for v in DATA["navy"].values())
        self.assertEqual(nominal, 45100)
        self.assertLessEqual(abs(nominal - DATA["active_force"]["navy_crews"]), 100)

    def test_argo_superior_status_is_not_assumed_for_enemy_airships(self):
        self.assertFalse(DATA["experimental_aerial"]["argos_technology_equivalent_confirmed"])
        self.assertFalse(DATA["experimental_aerial"]["global_supersonic_air_fleet_confirmed"])
        self.assertFalse(DATA["expedition_in_avaren_proposal"]["full_empire_on_avaren"])


if __name__ == "__main__":
    unittest.main()
