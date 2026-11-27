import copy
import unittest
from hashlib import sha256
from worldroot.omega_hybrid_receipt import validate_macro, sqlite_isolation, ARCHIVE

class HybridTests(unittest.TestCase):
    def setUp(self):
        self.m=dict(id="m",previous_macro="p",start=1,end=3,source="s",unit_seal="u")
        self.h=lambda s:sha256(s.encode()).hexdigest()
        self.source=(("## Response:","synthetic claim",""),("Response",)*3,((1,3,"blob"),),"src")
        e=dict(source="s",source_sha256_manifest="src",blob_sha1="blob",line_start=1,line_end=2,role="Response",span_sha256_utf8=self.h("## Response:\nsynthetic claim"))
        me=dict(e,line_start=3,line_end=3,span_sha256_utf8=self.h(""))
        self.r=dict(schema="OMEGA_TURBO_V3_COMPLETE_MACRO_EDITORIAL_RECEIPT_V1",project="CRONICAS_DE_UM_NOVO_MUNDO",archive_pin=ARCHIVE,macro_id="m",previous_macro_id="p",range=[1,3],source="s",source_sha256="src",next_line=4,official_unit_seal="u",canon_changed=False,semantic_certification=False,records=[dict(id="r",book="III",day=1,authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",type="character",promotion=False,evidence=e,axes=[1])],coverage=[dict(start=1,end=2,role="Response",span_sha256_utf8=e["span_sha256_utf8"],record_ids=["r"]),dict(start=3,end=3,role="Response",span_sha256_utf8=me["span_sha256_utf8"],record_ids=[],disposition="NON_NARRATIVE_METADATA")],metadata=[dict(range=[3,3],disposition="NON_NARRATIVE_METADATA",evidence=me)],axis_coverage=dict(assessed=list(range(1,31)),represented=[1]))
        self.o={"r":dict(macro=25,day=1,authority=self.r["records"][0]["authority"],visibility=self.r["records"][0]["visibility"],effective_axes=[1],promotion=False,disposition="STAGING_HISTORICAL_CANDIDATE_NO_PROJECTION")}
    def run_check(self):
        return validate_macro(self.r,self.m,25,{},self.o,self.source)
    def test_native_literal_and_sqlite(self):
        rows,axes,meta=self.run_check()
        self.assertEqual((len(rows),axes[1],meta),(1,1,1))
        self.assertEqual(sqlite_isolation(rows,self.o)["typed_events"],0)
    def test_partial_overlay_no_mutation(self):
        self.r["records"][0].pop("axes")
        self.r["axis_overlay_original_partial"]=[dict(id="r",axes=[1])]
        before=copy.deepcopy(self.r)
        self.run_check()
        self.assertEqual(before,self.r)
    def test_unselected_not_event(self):
        self.r["records"][0]["authority"]="NARRATOR_PROPOSED_BRANCH_NOT_EVENT"
        self.o["r"].update(authority="NARRATOR_PROPOSED_BRANCH_NOT_EVENT",disposition="NON_EVENT_OR_GAP_NO_PROJECTION")
        self.run_check()
        self.o["r"]["disposition"]="STAGING_HISTORICAL_CANDIDATE_NO_PROJECTION"
        with self.assertRaises(ValueError):self.run_check()
    def test_bad_anchor(self):
        self.r["records"][0]["evidence"]["span_sha256_utf8"]="0"*64
        with self.assertRaises(ValueError):self.run_check()
    def test_explicit_join_without_single_primary(self):
        self.source=(self.source[0],self.source[1],((1,1,"blob"),(2,3,"other")),"src")
        self.r["records"][0]["evidence"].update(blob_sha1=None,source_blob_sha1s=["blob","other"])
        self.r["metadata"][0]["evidence"]["blob_sha1"]="other"
        self.run_check()
        self.r["records"][0]["evidence"]["source_blob_sha1s"]=["blob"]
        with self.assertRaises(ValueError):self.run_check()
    def test_null_primary_single_part_rejected(self):
        self.r["records"][0]["evidence"].update(blob_sha1=None,source_blob_sha1s=["blob"])
        with self.assertRaises(ValueError):self.run_check()
    def test_bad_physical_blob(self):
        self.r["records"][0]["evidence"]["blob_sha1"]="other"
        with self.assertRaises(ValueError):self.run_check()
    def test_promotion(self):
        self.r["records"][0]["promotion"]=True
        with self.assertRaises(ValueError):self.run_check()
    def test_metadata_omission(self):
        self.r["metadata"]=[]
        with self.assertRaises(ValueError):self.run_check()
    def test_private_leak(self):
        self.r["records"][0]["type"]="reader_scene"
        with self.assertRaises(ValueError):self.run_check()
    def test_bad_axis(self):
        self.o["r"]["effective_axes"]=[2]
        with self.assertRaises(ValueError):self.run_check()
    def test_gap(self):
        self.r["coverage"][1]["start"]=2
        with self.assertRaises(ValueError):self.run_check()
    def test_no_replace_inline_axes(self):
        self.r["axis_overlay_original_partial"]=[dict(id="r",axes=[1])]
        with self.assertRaises(ValueError):self.run_check()
    def test_bad_chain(self):
        self.r["previous_macro_id"]="wrong"
        with self.assertRaises(ValueError):self.run_check()

if __name__=="__main__":unittest.main()
