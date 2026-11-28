"""Reconstruct the validated FC01 locator map without publishing corpus or identities."""
import argparse,json
from pathlib import Path
from . import omega_global_p0 as p0,omega_global_p1a as a1,omega_final_convergence as fc
from .omega_final_runtime import eligible
from .omega_hybrid_receipt import ROOT,ARCHIVE,read
from .omega_turbo_recovery import digest,require
from . import live_codex as codex
CP="4ccd39bc6dc0ca7f5bf2e6884b1d3a16b3c18474"
def export(root,archive):
    cp=read(root,ROOT+"fc01-checkpoint-v1.json",CP)
    ev=read(root,cp["evidence_path"],cp["evidence_blob"])
    require(ev["workflow_conclusion"]=="success" and ev["aggregate"]==cp["metrics"],"FC01 evidence")
    got={}
    inv=p0.inspect(root,archive,inventory_consumer=lambda rows,groups,partition:got.update(rows=rows))
    previous=read(root,ROOT+"global-p1-b-batch-001-sublot-001-checkpoint-v1.json",fc.P1B)
    prepared={r["id"] for r in got["rows"] if r["receipt_blob"] in a1.PARENTS.values()}|set(previous["completed_ids"])
    reg,binding=codex.load_registry(archive)
    rows,links=fc.reconcile(got["rows"],list(codex.all_records(reg)),prepared)
    require(binding==fc.BINDING and inv["inventory_sha256"]==cp["metrics"]["inventory_sha256"] and digest(p0.stable(rows))==cp["metrics"]["map_sha256"] and digest(p0.stable(links))==cp["metrics"]["links_sha256"],"FC01 authority")
    out=[]
    for r in rows:
        if not eligible(r):continue
        out.append({**{k:r[k] for k in ("id","macro","source","source_sha256","interval","anchor","physical_blobs","role","authority","visibility","review_route")},"candidate_ids":sorted({i for l in r["labels"] for i in l["candidate_ids"]})})
    require(len(out)==3387,"eligible denominator")
    body={"schema":"worldroot-fc-operational-locators-v1","project":p0.PROJECT,"archive_pin":ARCHIVE,"registry_binding":binding,"inventory_sha256":inv["inventory_sha256"],"map_sha256":cp["metrics"]["map_sha256"],"groups":out}
    return {**body,"pack_sha256":digest(p0.stable(body))}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    path=Path(a.output).resolve();require(not path.is_relative_to(Path(a.archive_root).resolve()) and not path.is_relative_to(Path(a.engine_root).resolve()),"ephemeral path required")
    pack=export(a.engine_root,a.archive_root)
    with path.open("x",encoding="utf-8") as f:json.dump(pack,f,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    print(json.dumps({"groups":len(pack["groups"]),"pack_sha256":pack["pack_sha256"],"canon_changed":False},sort_keys=True))
if __name__=="__main__":main()
