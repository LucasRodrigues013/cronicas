import sqlite3,unittest
from worldroot.omega_historical_recovery import alias_index,matcher,mentions,line_rows,initialize,lookup,sha
class HistoricalRecovery(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(id="one",name="AERÚN",aliases=["Instituto AERÚN"],domains=["Atlas mundial"]),
                   dict(id="two",name="AERÚN",aliases=[],domains=["Personagens"]),
                   dict(id="varo",name="Varo",aliases=[],domains=["Personagens"]),
                   dict(id="spell",name="Luz",aliases=[],scope="GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE")]
        self.idx=alias_index(self.rows);self.pattern=matcher(self.idx)
    def test_ambiguous_not_resolved(self):
        self.assertEqual(list(mentions("AERÚN",self.idx,self.pattern)),[("aerun",["one","two"],"AMBIGUOUS_ALIAS",False)])
    def test_longest_specific_alias(self):
        self.assertEqual(list(mentions("Instituto AERÚN",self.idx,self.pattern))[0][1],["one"])
    def test_word_boundary(self):
        self.assertEqual(list(mentions("Varoa",self.idx,self.pattern)),[])
    def test_unregistered_speaker(self):
        self.assertEqual(list(mentions("**OSVAN —** Bom dia.",self.idx,self.pattern)),[("osvan",[],"UNREGISTERED_MENTION",True)])
    def test_no_proposed_spell(self):
        self.assertEqual(list(mentions("Luz",self.idx,self.pattern)),[])
    def test_source_role_and_line_hash(self):
        lines=["Varo\\n","**OSVAN —** Olá.\\n"]
        out=list(line_rows("TRANSCRIPT","s","a"*64,"Prompt",17,lines,self.idx,self.pattern))
        self.assertEqual(out[0][3:6],("Prompt",17,sha(lines[0])))
        self.assertEqual(out[1][3:6],("Prompt",18,sha(lines[1])))
    def test_stale_lookup(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT)")
            initialize(db)
            with self.assertRaises(ValueError):lookup(db,"Varo")
if __name__=="__main__":unittest.main()
