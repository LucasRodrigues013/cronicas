import unittest
from worldroot.omega_bulk_recovery import AXES, axis_hits, build_units, pack, seal, digest_text
from worldroot.omega_historical_recovery import matcher

class OmegaBulkRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.idx={"varo":{"varo"},"alias":{"a","b"}}
        self.p=matcher(self.idx)
    def units(self,body,regions=None,**kw):
        return build_units("fixture","a"*64,body,regions or [(1,len(body.splitlines()),"I","PENDING")],self.p,self.idx,**kw)
    def test_all_30_axes_declared(self):
        self.assertEqual(set(AXES),set(range(1,31)))
    def test_role_coverage_and_no_raw(self):
        body="## Prompt:\nquero Varo\n## Response:\nVaro retorna.\n"
        u=self.units(body,max_lines=1)
        self.assertEqual([x["role"] for x in u],["Prompt","Prompt","Response","Response"])
        self.assertEqual([x["start"] for x in u],[1,2,3,4])
        self.assertEqual(u[1]["authority"],"AUTHOR_DIRECTION_NOT_EVENT")
        self.assertEqual(u[1]["anchor_sha256"],digest_text("quero Varo\n"))
        self.assertNotIn("quero Varo",str(u))
        self.assertTrue(all(not x["promotion"] for x in u))
    def test_region_break_context_and_resume(self):
        u=self.units("## Response:\na\nb\nc\n",[(1,2,"I","CONTROLLER_REVIEWED_PREFIX"),(3,4,"I","PENDING")])
        self.assertEqual([(x["start"],x["end"]) for x in u],[(1,2),(3,4)])
        self.assertEqual(u[1]["context_start"],3)
        self.assertEqual(pack(u)[1]["start"],3)
        self.assertEqual(pack(u)[1]["previous_macro"],pack(u)[0]["id"])
    def test_stable_and_tamper_sensitive(self):
        a=self.units("## Response:\nVaro\n")
        self.assertEqual(seal(a),seal(self.units("## Response:\nVaro\n")))
        self.assertNotEqual(seal(a),seal(self.units("## Response:\nKael\n")))
    def test_ambiguity_not_resolution(self):
        u=self.units("## Response:\nalias\n")[0]
        self.assertEqual(u["ambiguous_alias_count"],1)
        self.assertEqual(u["entity_candidate_count"],2)
    def test_macro_ceiling_and_total(self):
        body="## Response:\n"+"dia batalha Varo\n"*42000
        u=self.units(body);m=pack(u)
        self.assertEqual(sum(x["lines"] for x in m),42001)
        self.assertTrue(all(x["lines"]<=20000 for x in m))
        self.assertTrue(all(x["lines"]>=10000 for x in m[:-1]))
    def test_duplicate_text_kept(self):
        u=self.units("## Response:\nmesma\nmesma\n",max_lines=1)
        self.assertEqual(u[1]["anchor_sha256"],u[2]["anchor_sha256"])
        self.assertNotEqual(u[1]["id"],u[2]["id"])
    def test_invalid_gap(self):
        with self.assertRaises(ValueError): self.units("a\nb\n",[(2,2,"I","PENDING")])
    def test_large_single_line_not_dropped(self):
        u=self.units("x"*200,max_chars=100)
        self.assertTrue(u[0]["oversized_line"])
        self.assertEqual(u[0]["end"],1)
    def test_no_hits_is_not_absence(self):
        self.assertEqual(axis_hits("xyz"),[])
        self.assertFalse(self.units("xyz")[0]["promotion"])
