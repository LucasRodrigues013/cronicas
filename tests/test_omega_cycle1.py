"""OMEGA cycle 1: public synthetic regression only, no historical text."""
import copy
import hashlib
import sqlite3
import json
import unittest
from worldroot import semantic_queue as q
from worldroot import r36_benchmark as b
from worldroot import r36_experiment as x
from worldroot import r36_temporal as t
from worldroot.live_codex import initialize

def row(**kw):
    v=dict(original_id=1,entity_id="fixture",field="role",source="fixture",
        source_sha256="a"*64,source_status="CLOSED",day=1,line=1,
        anchor="Synthetic witness arrived.",anchor_sha256="b"*64,
        context=[{"line":1,"text":"Synthetic witness arrived."}])
    v.update(kw);return v

def answer(job):
    return dict(job_id=job["job_id"],executor="fixture-A",model_revision="fixture",
        source_role="NARRATED",role_reason="synthetic",decisions=[
        dict(original_id=1,entity_id="fixture",field="role",verdict="SUPPORTED",
        reason="synthetic",claim="arrived",evidence="Synthetic witness arrived.")])

def case(i,split="development",**kw):
    v=dict(id="case-"+str(i),category="memory",family="family-"+str(i),
        episodes=["episode-"+str(i)],entities=["entity-"+str(i)],
        source_pins=[hashlib.sha256(str(i).encode()).hexdigest()],split=split,severity="major")
    v.update(kw);return v

def experiment():
    common={k:"d"*64 for k in x.PINS-{"case_ids","split"}}
    common.update(case_ids=["one"],split="development")
    return x.freeze("a"*64,"b"*64,common,{"fixture":True})

def metric(**kw):
    m={k:1 for k in x.FIELDS-{"case_id","input_sha","outcome"}}
    m.update(case_id="one",input_sha="c"*64,outcome="DECISIVE",critical=0)
    m.update(kw);return m

class OmegaRegression(unittest.TestCase):
    def test_sealed_job(self):
        j=list(q.jobs([row()]))[0];a=answer(j)
        self.assertEqual(q.validate(j,a),a)
        for k,v in [("day",2),("source_status","HISTORICAL_RESPONSE_UNREVIEWED"),
                    ("source_sha256","f"*64),("anchor","changed"),
                    ("context",j["context"]+[{"line":2,"text":"Untrusted extra context."}])]:
            with self.subTest(field=k),self.assertRaises(ValueError):
                q.validate({**j,k:v},a)

    def test_conflicting_group(self):
        for k,v in [("day",2),("source_status","PENDING_NOT_CLOSED"),("anchor","different")]:
            with self.subTest(field=k),self.assertRaises(ValueError):
                list(q.jobs([row(),row(original_id=2,**{k:v})]))

    def test_metadata_whitespace(self):
        for field in ("family","episodes","entities","id"):
            for pad in (" ","\t","\n"):
                a=case(1)
                val=a[field]
                other=case(2,"validation",**{field:([pad+val[0]] if isinstance(val,list) else pad+val)})
                with self.subTest(field=field,pad=repr(pad)),self.assertRaises(ValueError):
                    b.validate_inventory([a,other],exact=False)
        self.assertEqual(b.validate_inventory([case(1),case(2,"validation")],exact=False)["cases"],2)

    def test_paired_author_denominator(self):
        with self.assertRaises(ValueError):
            x.paired_metrics(experiment(),[metric(author_agree=1,author_total=2)],
                            [metric(author_agree=1,author_total=1)])
        self.assertEqual(x.paired_metrics(experiment(),[metric()],[metric()])["challenger"]["author_agreement"],1)

class OmegaTemporalStress(unittest.TestCase):
    def test_synthetic_horizons(self):
        # Same schema and query used by runtime, isolated in-memory SQLite.
        # 100 temporal queries per horizon, each checked against independent
        # arithmetic oracle; not 300 historical questions or model outputs.
        for horizon in (1000,2000,5000):
            with self.subTest(horizon=horizon):
                db=sqlite3.connect(":memory:")
                try:
                    initialize(db)
                    db.execute("INSERT INTO records VALUES(?,?,?)",("assets","fixture","{}"))
                    closures=[]
                    for d in range(1,horizon+1):
                        clock="09h00" if d%3 else None
                        scope="PRIVATE_CHARACTER" if d%7==0 else "WORLD"
                        eid="e"+str(d)
                        db.execute("INSERT INTO codex_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (eid,"ep"+str(d),d,0,d,clock,"fixture","ACQUIRE",json.dumps({"scope":scope}),"sha",1,"anchor"))
                        db.execute("INSERT INTO codex_event_entities VALUES(?,?,?)",(eid,"fixture","ITEM"))
                        closures.append(dict(episode_id="ep"+str(d),sequence=d,story_sha256="sha",metadata={"day":d},
                            events=[dict(event_id="c"+str(d),visibility="PUBLICO",clock=clock,occurred_day=d,
                                summary_candidato="fixture",source=dict(sha256="sha",line=1,literal_anchor="anchor"))]))
                    for repetition in range(2):
                        result=t.rebuild(db,closures)
                        self.assertEqual(result["canonical_events"],horizon)
                        self.assertEqual(result["shared_anchor_events"],horizon)
                        self.assertFalse(result["semantic_certification"])
                    for i in range(100):
                        day=1+(i*(horizon-1))//99
                        clock=("08h59","09h00",None)[i%3]
                        limit=(1,10,50)[i%3]
                        expected=[d for d in range(day,0,-1) if d%7 and
                            (d<day or clock is None or (d%3 and clock>="09h00"))][:limit]
                        got=t.entity_history(db,"fixture",day,clock,limit)
                        self.assertEqual([v["day"] for v in got],expected)
                        self.assertTrue(all(v["shared_public_source_anchors"]==["c"+str(v["day"])] for v in got))
                    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
                    self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(),[])
                finally:db.close()
