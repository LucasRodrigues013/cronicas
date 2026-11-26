import unittest
from worldroot.world_coherence import passage,seating,combat,validate_interactions,learned_in_registry

class CoherenceTests(unittest.TestCase):
    # Synthetic measurement profiles, NOT canonized character dimensions.
    def setUp(self):
        self.large={"height_cm":224,"shoulder_width_cm":70,"mass_kg":170,"seated_width_cm":60,"comfortable_seat_height_cm":60}
        self.small={"height_cm":150,"shoulder_width_cm":42,"mass_kg":72,"seated_width_cm":38,"comfortable_seat_height_cm":35}
        self.human_door={"clear_height_cm":205,"clear_width_cm":85}
        self.dwarf_door={"clear_height_cm":160,"clear_width_cm":80}
        self.human_seat={"rated_mass_kg":110,"seat_width_cm":45,"seat_height_cm":45}
    def test_kairon_upright_normal_door(self):
        self.assertEqual(passage(self.large,self.human_door)["status"],"BLOCKED")
    def test_known_lower_bound_blocks_short_door(self):
        self.assertEqual(passage({"height_lower_bound_cm":200},self.dwarf_door)["status"],"BLOCKED")
    def test_bending_is_not_magic_shrinking(self):
        self.assertEqual(passage(self.large,self.human_door,"stoop")["status"],"UNKNOWN")
        self.assertEqual(passage({**self.large,"posture_height_cm":193},self.human_door,"stoop")["status"],"POSSIBLE")
    def test_large_seat_load(self):
        self.assertEqual(seating(self.large,self.human_seat)["reason"],"load")
    def test_short_seat_ergonomics(self):
        self.assertEqual(seating(self.small,self.human_seat)["status"],"ADAPTATION_REQUIRED")
    def test_unknown_mass_not_safe(self):
        self.assertEqual(seating({"height_cm":224},self.human_seat)["status"],"UNKNOWN")
    def test_vehicle_hatch_and_width(self):
        self.assertEqual(passage({**self.large,"posture_height_cm":170},{"clear_height_cm":180,"clear_width_cm":55},"stoop")["reason"],"width")
    def test_mosquito_dragon_direct_channel(self):
        self.assertEqual(combat(0,6,channel="direct physical damage",access=True,ability_proven=True)["status"],"BLOCKED")
    def test_hero_cannot_invent_power(self):
        self.assertEqual(combat(7,3,channel="arcane",access=True,ability_proven=False)["reason"],"unproven_capability")
    def test_unknown_dragon_defense_not_assumed(self):
        self.assertEqual(combat(3,None,channel="arcane",access=True,ability_proven=True)["status"],"UNKNOWN")
    def test_equal_scale_not_guaranteed_victory(self):
        self.assertEqual(combat(4,4,channel="physical",access=True,ability_proven=True)["status"],"POSSIBLE_NOT_GUARANTEED")
    def test_research_link_is_not_magic_acquisition(self):
        self.assertFalse(learned_in_registry({"research_links":[{"school_id":"x"}]},"spell"))
    def test_scene_cannot_override_dimensions(self):
        c={"actor":"a","target":"b","kind":"PASSAGE","disposition":"SUPPORTED","line":1,"anchor":"A entrou.","reason":"Abertura livre","inputs":{"height_cm":1}}
        with self.assertRaisesRegex(ValueError,"override"):
            validate_interactions("A entrou.",{"schema":"worldroot-coherence-review-v1","coverage_reason":"fixture","interactions":[c]},{"a":{},"b":{}})
