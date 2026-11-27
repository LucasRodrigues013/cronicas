import copy
import unittest
from worldroot.omega_book_iv_handoff import registry_matches, plan_scope
from worldroot.omega_hybrid_receipt import read

class BookIVHandoffTests(unittest.TestCase):
    def setUp(self):
        self.q=read(".","audit/omega008-c/bulk-macro-queue.json")["macros"]
        self.registry={"records":[{"id":"a","name":"AERÚN"},{"id":"b","name":"AERÚN"}],
                       "species":[],"arcane":{"schools":[],"index":[]}}
        self.c=[{"raw_key":"aerun","candidate_ids":["a","b"],"status":"AMBIGUOUS_KEEP_UNRESOLVED","promotion":False}]
    def test_scope(self):
        self.assertEqual(plan_scope(self.q)["macros"],13)
        self.assertEqual(plan_scope(self.q)["first_range"],[268704,279001])
    def test_bad_chain(self):
        self.q[31]["previous_macro"]="invalid"
        with self.assertRaises(ValueError):plan_scope(self.q)
    def test_lot_not_pending(self):
        self.q[29]["status"]="COMPLETE"
        with self.assertRaises(ValueError):plan_scope(self.q)
    def test_source_gap(self):
        self.q[30]["start"]+=1;self.q[30]["lines"]-=1
        with self.assertRaises(ValueError):plan_scope(self.q)
    def test_homonym(self):
        self.assertEqual(registry_matches(self.registry,self.c)["ambiguous"],1)
    def test_forced_merge(self):
        self.c[0]["candidate_ids"]=["a"]
        with self.assertRaises(ValueError):registry_matches(self.registry,self.c)
    def test_fabricated_identity(self):
        self.c[0]["candidate_ids"]=["a","missing"]
        with self.assertRaises(ValueError):registry_matches(self.registry,self.c)
    def test_promotion(self):
        self.c[0]["promotion"]=True
        with self.assertRaises(ValueError):registry_matches(self.registry,self.c)
    def test_duplicate_key(self):
        self.c.append(copy.deepcopy(self.c[0]))
        with self.assertRaises(ValueError):registry_matches(self.registry,self.c)

if __name__=="__main__":unittest.main()
