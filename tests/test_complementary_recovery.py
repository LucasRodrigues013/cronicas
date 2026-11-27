import unittest
from worldroot.complementary_recovery import scenes,candidates
class ComplementaryTests(unittest.TestCase):
    def test_partition(self):
        s=scenes("intro\n12h18 | A\ntext\n13h00 | B",3,"source")
        self.assertEqual([(x["start"],x["end"]) for x in s],[(1,1),(2,3),(4,4)])
    def test_gate_and_dedup(self):
        x=dict(name="Manta",domain="world",line=1,anchor="Manta",scope="RESTRICTED",role="NARRATED",day=206)
        a=candidates("Manta",3,"s",[x,x],["manta"])
        self.assertEqual(len(a),1)
        self.assertTrue(a[0]["registry_match"])
        self.assertEqual(a[0]["status"],"AUTHOR_GATE_PENDING")
        self.assertEqual(a[0]["scope"],"RESTRICTED")
        with self.assertRaises(ValueError):
            candidates("other",3,"s",[x],[])
