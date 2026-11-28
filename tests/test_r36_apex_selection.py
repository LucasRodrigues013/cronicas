import unittest
from worldroot.r36_apex_selection import select
def row(id,source,span,terms,ids=(),macro=1,flags=("NARRATIVE_CANDIDATE",)):
    r=dict(id=id,source=source,interval=span,candidate_ids=list(ids),macro=macro)
    return (r,[(span[0],set(terms),flags)],set(terms))
class Apex(unittest.TestCase):
    def test_same_source_complementary(self):
        rows=[row("a","s",[1,4],["alpha"]),row("b","s",[10,14],["beta"]),row("c","t",[1,4],["alpha"])]
        out=select(rows,{"alpha","beta"},set(),True,"coverage",2)
        self.assertEqual({r["id"] for r,_ in out},{"a","b"})
    def test_overlap_and_determinism(self):
        rows=[row("a","s",[1,8],["alpha"]),row("b","s",[2,7],["alpha"]),row("c","s",[20,21],["alpha"])]
        for mode in ("fusion","coverage"):
            a=select(rows,{"alpha"},set(),True,mode,3)
            self.assertEqual(a,select(list(reversed(rows)),{"alpha"},set(),True,mode,3))
            self.assertEqual(len(a),2)
    def test_negation_retained(self):
        r=row("a","s",[1,4],["alpha"],flags=("NEGATION_CUE",))
        self.assertEqual(select([r],{"alpha"},set(),True)[0][1][2],("NEGATION_CUE",))
    def test_no_lexical_evidence_no_identity_inference(self):
        self.assertEqual(select([row("a","s",[1,4],["beta"],["id"])],{"alpha"},{"id"},True),[])
    def test_bounds(self):
        for mode,limit in (("unknown",3),("fusion",0),("fusion",11)):
            with self.assertRaises(ValueError):select([],{"a"},set(),False,mode,limit)
    def test_alias_disabled(self):
        rows=[row("a","s",[1,4],["alpha"],["id"]),row("b","t",[1,4],["alpha"])]
        self.assertEqual(select(rows,{"alpha"},{"id"},False),select(rows,{"alpha"},set(),False))
