import unittest
from worldroot.omega_global_p1b import validate_spec,geometry
class P1B(unittest.TestCase):
    def parent(self,role="Response",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED"):
        return {"authority":authority,"evidence":{"line_start":10,"line_end":20,"role":role}}
    def test_prompt(self):
        with self.assertRaises(ValueError):validate_spec(["x","p",True,"NARRATED",10,10],self.parent("Prompt","AUTHOR_DIRECTION_NOT_EVENT"))
    def test_bounds(self):
        with self.assertRaises(ValueError):validate_spec(["x","p",True,"NARRATED",9,10],self.parent())
    def test_age(self):
        with self.assertRaises(ValueError):validate_spec(["x","biological_age_years",40,"NARRATED",10,10],self.parent())
    def test_unknown_age(self):
        self.assertIsNone(validate_spec(["x","biological_age_years",None,"NARRATED",10,10],self.parent())[2])
    def test_scope(self):
        with self.assertRaises(ValueError):validate_spec(["x","p",True,"REPORT",10,10],self.parent("Response","NARRATOR_PROPOSED_BRANCH_NOT_EVENT"))
    def test_gap(self):
        r=[{"id":"a","evidence":{"line_start":2,"line_end":3}}]
        geometry(r,["a"],[[1,1,"meta"],[4,4,"gap"]],[1,4])
        with self.assertRaises(ValueError):geometry(r,["a"],[[1,1,"meta"]],[1,4])
    def test_duplicate(self):
        r=[{"id":"a","evidence":{"line_start":2,"line_end":3}}]
        with self.assertRaises(ValueError):geometry(r,["b"],[[1,1,"meta"]],[1,3])
    def test_overlap(self):
        r=[{"id":"a","evidence":{"line_start":2,"line_end":3}}]
        with self.assertRaises(ValueError):geometry(r,["a"],[[1,2,"meta"]],[1,3])
