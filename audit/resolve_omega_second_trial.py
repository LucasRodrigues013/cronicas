"""Resolve the actual ambiguity diagnostics from the second R36 trial.
New immutable request ID, same historical source selection and new author plan.
No old production preparation, no story writes.
"""
import argparse, json, shutil, tempfile, time
from pathlib import Path
from audit.run_omega_second_trial import make_request, stamp, load
from worldroot.git_cycle import canonical
from worldroot.live_codex import sync
from worldroot.r33_runtime import prepare_from_request, digest
ID="LVI-C09-PII-D580-OMEGA-SECOND-TRIAL-B"
PREVIOUS_REQUEST="b7b30cc163d36dc48c650888369c36e31d31d07ffb0b9ff3ce5643c4b19182b4"
# Exact IDs chosen by source context: civilian logistics sector, research
# institution, and real characters rather than plot records sharing aliases.
SCOPES=[
    {"scene":3,"ids":["campo-aurora"]},
    {"scene":5,"ids":["aerun-instituto"]},
    {"scene":6,"ids":["varkhess","tharvek","bressa","velkar","ordan"]},
    {"scene":7,"ids":["aerun-instituto"]},
]
def run(root,out):
    start=time.perf_counter()
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        w=Path(d)/"archive";shutil.copytree(root,w,ignore=shutil.ignore_patterns(".git"))
        graph=sync(w);req=make_request(w)
        assert digest(req)==PREVIOUS_REQUEST
        req["delivery_id"]=ID;req["world_scope"]=SCOPES
        (w/"requests"/(ID+".json")).write_bytes(canonical(req))
        r=prepare_from_request(w,req);packet=load(w/"preparations"/(ID+".json"))
        assert r["preparation_sha256"]==packet["preparation_sha256"]
        scenes=packet["universal_codex"]["scene_context"]["scenes"]
        ambiguities=sum(len(x["ambiguities"]) for x in scenes)
        assert ambiguities==0
        assert all(x["source_status"]=="CLOSED_GRAPH_AND_EDITORIAL_CANDIDATES" for x in scenes)
        assert all(len(x["ids"])==1 for x in packet["universal_codex"]["focal"])
        (out/"request.json").write_bytes(canonical(req))
        (out/"preparation.json").write_bytes(canonical(packet))
        stamp("resolved_fresh_preparation",start,previous_request=PREVIOUS_REQUEST,
              request_sha256=digest(req),preparation_sha256=r["preparation_sha256"],
              editorial_receipt_sha256=r["editorial_receipt_sha256"],ambiguities=ambiguities,
              verified=packet["memory"]["verified"],required=packet["memory"]["required"],
              graph_records=graph["records"],typed_events=graph["events"],scenes=len(scenes),
              selected=[{"scene":s["scene"],"direct_ids":s["direct_ids"]} for s in scenes],
              semantic_certification=False,canon_changed=False,generation_executed=False)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--archive-root",type=Path,required=True);a.add_argument("--output",type=Path,required=True);n=a.parse_args();run(n.archive_root,n.output)
