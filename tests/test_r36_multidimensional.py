import unittest
from worldroot.r36_multidimensional import verify_observations, verify_protected_profiles
class MultidimensionalTests(unittest.TestCase):
    def test_anchor_and_order(self):
        a={"line":2,"anchor":"B","scope":"UNKNOWN","status":"AUTHOR_GATE_PENDING"}
        b={**a,"line":1,"anchor":"A"}
        self.assertEqual([x["line"] for x in verify_observations("A\nB",[a,b])],[1,2])
        with self.assertRaises(ValueError): verify_observations("A\nB",[{**a,"anchor":"C"}])
        with self.assertRaises(ValueError): verify_observations("A\nB",[a,a])
    def test_protected(self):
        old={"x":{"knowledge":{"value":"secret","scope":"PRIVATE_CHARACTER"}}}
        with self.assertRaises(ValueError): verify_protected_profiles(old,{"x":{"knowledge":{"value":"new"}}},[("x","knowledge")])
        self.assertEqual(verify_protected_profiles(old,old),set())
    def test_unauthorized(self):
        old={"x":{"body":{"value":"old"}}}
        new={"x":{"body":{"value":"new"}}}
        with self.assertRaises(ValueError): verify_protected_profiles(old,new)
        self.assertEqual(verify_protected_profiles(old,new,[("x","body")]),{("x","body")})
