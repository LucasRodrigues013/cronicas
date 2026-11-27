"""Full real-source recovery audit; no raw transcripts or anchors in logs."""
import argparse,hashlib,json,shutil,sqlite3,tempfile,time
from pathlib import Path
from worldroot.live_codex import sync
from worldroot.omega_historical_recovery import rebuild,lookup,SourceReader,query_projection
from worldroot.git_cycle import load
def main(root):
    start=time.perf_counter()
    with tempfile.TemporaryDirectory() as t:
        w=Path(t)/"archive";shutil.copytree(root,w,ignore=shutil.ignore_patterns(".git"))
        graph=Path(t)/"graph.sqlite";sync(w,graph)
        with sqlite3.connect(graph) as db:
            before={table:db.execute("SELECT count(*) FROM "+table).fetchone()[0] for table in ("records","codex_events","codex_state","codex_pending","r36_canon_event")}
            now=time.perf_counter();result=rebuild(w,db);elapsed=time.perf_counter()-now
            print(json.dumps({"stage":"omega008_full_recovery","seconds":round(elapsed,6),**result},ensure_ascii=False),flush=True)
            assert len(result["sources"])==6 and result["closed_episodes"]==load(w/"canon/HEAD.json")["sequence"]
            assert result["public_events_with_candidate"]<=result["public_events_total"]
            assert before=={table:db.execute("SELECT count(*) FROM "+table).fetchone()[0] for table in before}
            assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
            for name in ("Lucas","Miren","Varo","Kael","Lysa","Astra","Osvan","Orelia","AERÚN","Campo Aurora","Bressa","Tharvek","Círan","Káiron","GÊNESE","Talis","Calderva"):
                now=time.perf_counter();r=lookup(db,name)
                print(json.dumps({"stage":"omega008_probe","name":name,"milliseconds":round(1000*(time.perf_counter()-now),4),"counts":r["counts"],"candidate_dispositions":sorted(set(x["disposition"] for x in r["references"])),"public_event_candidates_returned":len(r["public_event_candidates"])},ensure_ascii=False),flush=True)
            # Confirm literal readback of a real unresolved identity, not invented IDs.
            reader=SourceReader(w)
            osvan=lookup(db,"Osvan",limit=100)
            assert osvan["references"] and all(r["disposition"]=="UNREGISTERED_MENTION" for r in osvan["references"])
            checked=[reader.read(r) for r in osvan["references"]]
            assert all("osvan" in r["literal"].casefold() for r in checked)
            # Log only this fictional character's closed-source positions, not transcript text.
            print(json.dumps({"stage":"omega008_osvan_evidence","verified_lines":len(checked),"references":[{"source":r["source_id"],"line":r["line"],"anchor_sha":r["anchor_sha"]} for r in checked]},ensure_ascii=False),flush=True)
            bad=dict(osvan["references"][0],anchor_sha="0"*64)
            try:reader.read(bad)
            except ValueError:pass
            else:raise AssertionError("Forged anchor accepted")
            response=db.execute("SELECT source_kind,source_id,source_sha,role,line,anchor_sha,candidates,disposition,speaker_label FROM omega_source_mention WHERE mention='miren' AND source_kind='TRANSCRIPT' AND role='Response' LIMIT 1").fetchone()
            ref=dict(zip(("source_kind","source_id","source_sha","role","line","anchor_sha","candidates","disposition","speaker_label"),response))
            assert "miren" in reader.read(ref)["literal"].casefold()
            try:reader.read(dict(ref,role="Prompt"))
            except ValueError:pass
            else:raise AssertionError("Cross-role source accepted")
            print(json.dumps({"stage":"omega008_literal_readback","closed":len(checked),"transcript":1,"tampered_anchor_rejected":True,"role_swap_rejected":True}),flush=True)
            # Same sealed source; repeated query is idempotent.
            before_count=db.execute("SELECT count(*) FROM omega_source_mention").fetchone()[0]
            before_seal=db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()[0]
            before_lookup=lookup(db,"Osvan")
            # Full rebuild is intentionally measured once, then verify query is read-only.
            assert lookup(db,"Osvan")==before_lookup
            assert db.execute("SELECT count(*) FROM omega_source_mention").fetchone()[0]==before_count
            assert db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()[0]==before_seal
        assert query_projection(w,graph,"Osvan",limit=1,readback=True)["references"][0]["literal"]
        for rel in ("canon/HEAD.json","ops/RESUME.json"):
            assert (root/rel).read_bytes()==(w/rel).read_bytes()
    print(json.dumps({"stage":"omega008_complete","seconds":round(time.perf_counter()-start,6),"canon_changed":False,"semantic_certification":False}),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--archive-root",type=Path,required=True);main(a.parse_args().archive_root)
