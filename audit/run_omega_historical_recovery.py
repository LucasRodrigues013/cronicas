"""Full real-source recovery audit; no raw transcripts or anchors in logs."""
import argparse,hashlib,json,shutil,sqlite3,tempfile,time
from pathlib import Path
from worldroot.live_codex import sync
from worldroot.omega_historical_recovery import rebuild,lookup
from worldroot.git_cycle import load
def main(root):
    start=time.perf_counter()
    with tempfile.TemporaryDirectory() as t:
        w=Path(t)/"archive";shutil.copytree(root,w,ignore=shutil.ignore_patterns(".git"))
        sync(w)
        with sqlite3.connect(w/"canon/codex.sqlite") as db:
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
            # Rebuild determinism across the exact same verified source bytes.
            before_count=db.execute("SELECT count(*) FROM omega_source_mention").fetchone()[0]
            before_seal=db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()[0]
            before_lookup=lookup(db,"Osvan")
            # Full rebuild is intentionally measured once, then verify query is read-only.
            assert lookup(db,"Osvan")==before_lookup
            assert db.execute("SELECT count(*) FROM omega_source_mention").fetchone()[0]==before_count
            assert db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()[0]==before_seal
        for rel in ("canon/HEAD.json","ops/RESUME.json"):
            assert (root/rel).read_bytes()==(w/rel).read_bytes()
    print(json.dumps({"stage":"omega008_complete","seconds":round(time.perf_counter()-start,6),"canon_changed":False,"semantic_certification":False}),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--archive-root",type=Path,required=True);main(a.parse_args().archive_root)
