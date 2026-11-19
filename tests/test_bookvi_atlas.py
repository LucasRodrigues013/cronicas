"""Fast deterministic tests; all fictional geography remains pre-canon proposal."""
from __future__ import annotations

import unittest

from worldroot.bookvi_atlas import (
    load, validate, direct_distance, route, travel, argos_block, city_transit,
)


class BookVIAtlasProposalTests(unittest.TestCase):
    def test_geometry_and_status_are_explicitly_provisional(self):
        out = validate()
        self.assertEqual(out["status"], "VALIDATED_AS_PROPOSAL", out["errors"])
        self.assertFalse(out["canon_promoted"])
        self.assertEqual(out["node_count"], 18)
        self.assertEqual(out["edge_count"], 22)
        self.assertIsNone(load()["canonical"]["argos_certified_cruise_kmh"])

    def test_canon_anchor_d522_eixo_is_not_grande_avenida(self):
        d = load()
        self.assertEqual(d["canonical"]["avenida_km"], 8)
        self.assertEqual(d["canonical"]["eixo_aurora_km"], 33.2)
        self.assertEqual(d["canonical"]["eixo_urbano_km"] + d["canonical"]["eixo_rural_km"], 33.2)
        self.assertEqual(round(direct_distance("TA", "CA")), 24)

    def test_thalor_seven_day_road_is_possible(self):
        t = route("TA", "TH")
        self.assertEqual(t["distance_km"], 320)
        self.assertEqual(t["path"], ["TA", "PL", "TH"])
        self.assertAlmostEqual(travel("TA", "TH")["days"], 7.11, places=2)

    def test_calderva_and_velath_trip_proposals(self):
        self.assertEqual(route("TA", "CV")["distance_km"], 545)
        self.assertEqual(route("TA", "VT")["distance_km"], 470)
        self.assertAlmostEqual(travel("TA", "CV")["days"], 12.11, places=2)
        self.assertEqual(travel("TA", "CV", transport="army")["days"], 24.77)

    def test_argos_must_depart_campo_not_city_center(self):
        for dest, minutes in [("TH", 71), ("CV", 99), ("VT", 83)]:
            flight = argos_block(dest)
            self.assertEqual(flight["origin"], "CA")
            self.assertEqual(flight["block_minutes"], minutes)
            self.assertTrue(flight["peak_D537_kmh_is_not_cruise"])
            self.assertTrue(flight["requires_external_landing_authorization"])

    def test_local_transit_time_templates_are_not_operating_service(self):
        self.assertEqual(city_transit(journey="old_avenue_end_to_end")["minutes"], 20)
        self.assertEqual(city_transit(journey="old_city_to_new_district")["minutes"], 45)
        self.assertAlmostEqual(city_transit(journey="civic_centre_to_campo")["minutes"], 71.4, places=1)
        self.assertEqual(city_transit(journey="civic_centre_to_campo")["status"], "PROPOSTA_DE_SERVICO_NAO_CIRCULANDO")

    def test_no_impossible_teleport_by_default(self):
        self.assertFalse(route("TA", "EL", mode="SEA")["reachable"])
        self.assertTrue(route("TA", "EL", mode="ROAD")["reachable"])
        with self.assertRaises(KeyError):
            route("TA", "VELKAR")
        with self.assertRaises(ValueError):
            travel("TA", "TH", transport="portal")


if __name__ == "__main__":
    unittest.main()
