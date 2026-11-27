"""Book IV preflight. Read-only; never recovers macro 0030 or opens production."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from .live_codex import norm
from .omega_turbo_recovery import require
from .omega_hybrid_receipt import ROOT, ARCHIVE, OVERLAY, REGISTRY, read, verify

PRIOR_CHECKPOINT = "322f816cad6e4e829760c1ec49406a2c43abcbc7"
QUEUE = "e5a5f9e358d20acf8559f6313c2da24b64665f48"
FIRST = "9860a957824d4b29700a03180af5af5f641a40d0bd5d6d71cb865db1fffa4002"
LAST_III = "a30708dd02e5b6fb0430f7b1c3ad9b2f81dd8272028e692c02a3cd36622e1792"


def plan_scope(macros):
    require(len(macros)>42 and macros[28]["id"]==LAST_III and macros[28]["end"]==268703,
            "Book III boundary")
    rows=macros[29:42]
    require(rows[0]["id"]==FIRST and rows[0]["start"]==268704 and rows[0]["end"]==279001,
            "Book IV opening")
    require(macros[42]["book_hint"]=="V" and macros[42]["previous_macro"]==rows[-1]["id"],
            "Book IV end boundary")
    previous=macros[28]; sources=[]
    for row in rows:
        require(row["book_hint"]=="IV" and row["status"]=="PENDING"
                and row["previous_macro"]==previous["id"],"Book IV chain or status")
        require(row["end"]-row["start"]+1==row["lines"],"Book IV geometry")
        if row["source"]==previous["source"]:
            require(row["start"]==previous["end"]+1,"Book IV source gap")
        else:
            require(row["start"]==1 and row["source"] not in sources,"Book IV source transition")
        if row["source"] not in sources:sources.append(row["source"])
        previous=row
    require(macros[42]["source"]==rows[-1]["source"] and
            macros[42]["start"]==rows[-1]["end"]+1,"Book V boundary")
    return {"macros":13,"first":30,"last":42,"lines":sum(x["lines"] for x in rows),
            "sources":len(sources),"first_range":[268704,279001],"first_unit_count":rows[0]["units"],
            "first_unit_seal":rows[0]["unit_seal"],"first_id":FIRST}


def registry_matches(registry,candidates):
    rows=registry["records"]+registry["species"]+registry["arcane"]["schools"]+registry["arcane"]["index"]
    ids={x["id"] for x in rows}
    require(len(ids)==len(rows),"duplicate registry ID")
    idx=defaultdict(set)
    for row in rows:
        for name in [row["id"],row["name"],*row.get("aliases",[])]:
            idx[norm(name)].add(row["id"])
    keys=set(); counts=Counter()
    for c in candidates:
        key=norm(c["raw_key"])
        require(key and key not in keys and c["promotion"] is False,"candidate authority")
        keys.add(key)
        given=c["candidate_ids"]
        require(len(given)==len(set(given)) and set(given)<=ids and set(given)==idx[key],
                "candidate lexical drift")
        status=("NO_LEXICAL_MATCH_KEEP_LOCAL" if not given else
                "AMBIGUOUS_KEEP_UNRESOLVED" if len(given)>1 else "SINGLE_LEXICAL_CANDIDATE_NOT_CONFIRMED")
        require(c["status"]==status,
                "candidate disposition")
        counts["unmatched" if not given else "single" if len(given)==1 else "ambiguous"]+=1
    return {"registry_ids":len(ids),"candidate_keys":len(keys),**dict(counts)}


def preflight(root, archive=None):
    root=Path(root)
    cp=read(root,ROOT+"book-III-native-staging-checkpoint.json",PRIOR_CHECKPOINT)
    require(cp["gate"]=="HOLD" and cp["next_macro_status"]=="NOT_STARTED" and cp["cursor"]==268704
            and cp["canon_changed"] is False and cp["official_checkpoint_changed"] is False,"checkpoint drift")
    previous=verify(root,archive)
    require(previous["records"]==886 and previous["coverage"]==395 and
            previous["sqlite"]["typed_events"]==0 and previous["gate"]=="HOLD","native staging drift")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json",QUEUE)["macros"]
    scope=plan_scope(q)
    o=read(root,ROOT+"book-III-consolidated-review-overlay.json",OVERLAY)
    controls=Counter(c["disposition"] for c in o["controls"])
    require(sum(controls.values())==45 and all(c["promotion"] is False for c in o["controls"]),"control guard")
    authorities=Counter(r["authority"] for r in o["records"])
    require(authorities["HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED"]==842 and sum(authorities.values())==886,
            "historical candidate counts")
    for r in o["records"]:
        require(r["promotion"] is False and r["visibility"].endswith("NO_CHARACTER_INJECTION"),"authority drift")
    native_registry=None
    if archive is not None:
        registry=read(Path(archive),"editorial/registries/universal-codex-design-d580-v1.json",REGISTRY)
        native_registry=registry_matches(registry,o["registry_candidates"])
        require(native_registry=={"registry_ids":1238,"candidate_keys":211,"single":46,"ambiguous":4,"unmatched":161},
                "registry inventory drift")
    # Even a successful private preflight produces no automatic recovery authorization.
    return {"state":"READY_FOR_MANUAL_GATE_REVIEW" if previous["literal_native_reverified"] and native_registry else
                    "PREFLIGHT_PREPARED_CUSTODY_HOLD",
            "book":"IV","scope":scope,"previous_native":previous,"controls":dict(controls),
            "candidate_authority":dict(authorities),"native_registry":native_registry,
            "typed_projection":False,"macro30_started":False,"recovery_authorized":False,
            "canon_changed":False,"official_checkpoint_changed":False,"production_gate":"HOLD"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--engine-root",default=".")
    p.add_argument("--archive-root",help="Authorized isolated private archive only")
    a=p.parse_args()
    print(json.dumps(preflight(a.engine_root,a.archive_root),sort_keys=True))


if __name__=="__main__":main()
