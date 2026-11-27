"""Read-only OMEGA Book III hybrid receipt adapter. No canonical writes."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import sqlite3
import subprocess

from .omega_turbo_recovery import SourceCache, anchor, git_blob, require
from .live_codex import initialize

ROOT = "audit/omega008-c/turbo-v3/"
ARCHIVE = "9dd632fb0bcd84dfce5b631013fdc67d7492ac5d"
DIAGNOSTIC = "d7bf3a9b26deec6e17fb77e69d70d53e35b5a8da"
OVERLAY = "84922e5c3f495482625865936eea718c6803f23b"
BASELINE = "30358c0192d501d4d9995b355b1106a35aa9a832"
REGISTRY = "3f004e6209a46b42a35291bb40fee8386bc7d6ca"
AXES = set(range(1,31))
SCHEMAS = {
    "worldroot-omega008-c-chronological-recovery-v1",
    "OMEGA_TURBO_V2_STAGED_GROUPED_RECEIPT",
    "OMEGA_TURBO_V3_COMPLETE_MACRO_EDITORIAL_RECEIPT_V1",
}
AUTHORITIES = {"AUTHOR_DIRECTION_NOT_EVENT","HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",
               "METADATA_NOT_EVENT","NON_NARRATIVE_SOURCE_GAP","NARRATOR_PROPOSED_BRANCH_NOT_EVENT"}
VISIBILITIES = {"EDITORIAL_ONLY_NO_CHARACTER_INJECTION","READER_ONLY_NO_CHARACTER_INJECTION",
                "RESTRICTED_KNOWLEDGE_NO_CHARACTER_INJECTION"}
PRIVATE_TYPES = {"reader-only","reader-perspectives","reader_scene","reader_perspective",
                 "reader_lore","private_knowledge","private_strategy","private_lore","dream","variant"}


def read(root, name, blob=None, digest=None):
    root = Path(root).resolve()
    p = (root / name).resolve()
    require(p.is_relative_to(root) and p.is_file(), "input path")
    raw = p.read_bytes()
    if blob is not None:
        require(git_blob(raw) == blob, "pinned blob")
    if digest is not None:
        require(sha256(raw).hexdigest() == digest, "pinned receipt hash")
    return json.loads(raw)


def axis_set(values):
    require(isinstance(values,list) and values and all(type(v) is int and v in AXES for v in values)
            and len(values)==len(set(values)), "invalid axes")
    return set(values)


def span(e, lo, hi, role, digest, bounds, source=None):
    require(type(lo) is int and type(hi) is int and bounds[0]<=lo<=hi<=bounds[1], "span bounds")
    require(role in {"Prompt","Response"} and isinstance(digest,str)
            and re.fullmatch("[0-9a-f]{64}",digest) is not None, "span metadata")
    if source is not None:
        require(all(x==role for x in source[1][lo-1:hi]), "source role")
        require(anchor(source,lo,hi)==digest, "literal source hash")
        if e is not None:
            actual={p[2] for p in source[2] if p[0]<=hi and p[1]>=lo}
            given=e.get("blob_sha1_parts",e.get("source_blob_sha1s",[e["blob_sha1"]]))
            primary=e["blob_sha1"]
            # A joined literal span can have no single principal physical blob.
            # Only accept null for an explicitly enumerated exact multi-part span.
            require(isinstance(given,list) and len(given)==len(set(given)) and set(given)==actual
                    and (primary in actual or (primary is None and len(actual)>1
                         and "source_blob_sha1s" in e and "blob_sha1_parts" not in e)),
                    "physical provenance")


def validate_macro(receipt, macro, number, correction, overlay_rows, source=None):
    r=receipt; bounds=[macro["start"],macro["end"]]
    require(r["schema"] in SCHEMAS and r["project"]=="CRONICAS_DE_UM_NOVO_MUNDO"
            and r["archive_pin"]==ARCHIVE, "receipt authority")
    require(r["macro_id"]==macro["id"] and r["previous_macro_id"]==macro["previous_macro"]
            and r["range"]==bounds and r["source"]==macro["source"]
            and r["next_line"]==bounds[1]+1, "macro chain")
    if "official_unit_seal" in r:
        require(r["official_unit_seal"]==macro["unit_seal"],"unit seal")
    require(r["canon_changed"] is False and r["semantic_certification"] is False
            and r.get("promotion",False) is False and r.get("independent_review",False) is False
            and r.get("official_checkpoint_changed",False) is False, "false authority")
    if source is not None:
        require(r["source_sha256"]==source[3],"source pin")
    partial={}
    for item in r.get("axis_overlay_original_partial",[]):
        require(item["id"] not in partial,"duplicate partial axis")
        partial[item["id"]]=axis_set(item["axes"])
    require(not partial or number==25,"unexpected partial overlay")
    additions={}
    if number==22:
        for item in correction["0022"]["records"]:
            rid=item["record_id"]
            require(rid not in additions and item["operation"]=="ADD_AXIS" and item["axis"]==6,"axis correction")
            additions[rid]=item
    rows={}; raw_union=set(); effective_union=set()
    used_partial=set(); used_additions=set(); counts=Counter()
    for rec in r["records"]:
        rid=rec["id"]; e=rec["evidence"]; lo=e["line_start"]; hi=e["line_end"]; role=e["role"]
        require(rid not in rows and rec["promotion"] is False and rec["book"]=="III","record identity")
        require(e["source"]==r["source"] and e["source_sha256_manifest"]==r["source_sha256"],"evidence source")
        span(e,lo,hi,role,e["span_sha256_utf8"],bounds,source)
        require(rec["authority"] in AUTHORITIES and rec["visibility"] in VISIBILITIES,"record authority")
        require((role=="Prompt")==(rec["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"prompt authority")
        require(rec["type"] not in PRIVATE_TYPES or rec["visibility"].startswith("READER_ONLY"),"private scope")
        if "axes" in rec:
            require(rid not in partial,"partial overlay replaces original axes")
            axes=axis_set(rec["axes"])
        else:
            require(rid in partial,"missing axes")
            axes=partial[rid]; used_partial.add(rid)
        raw_union.update(axes)
        effective=set(axes)
        if rid in additions:
            item=additions[rid]; a=item["evidence"]
            require(e["span_sha256_utf8"]==item["original_anchor_sha256"] and
                    rec["visibility"]==item["original_visibility"] and 6 not in axes
                    and lo<=a["line_start"]<=a["line_end"]<=hi and a["source"]==r["source"],"correction binding")
            span(None,a["line_start"],a["line_end"],role,a["span_sha256_utf8"],bounds,source)
            effective.add(6); used_additions.add(rid)
        effective_union.update(effective)
        projected=overlay_rows[rid]
        expected="STAGING_HISTORICAL_CANDIDATE_NO_PROJECTION" if rec["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" else "NON_EVENT_OR_GAP_NO_PROJECTION"
        require(projected["macro"]==number and projected["day"]==rec["day"]
                and projected["authority"]==rec["authority"] and projected["visibility"]==rec["visibility"]
                and projected["promotion"] is False and projected["disposition"]==expected
                and axis_set(projected["effective_axes"])==effective,"overlay drift")
        rows[rid]=rec; counts.update(effective)
    require(used_partial==set(partial) and used_additions==set(additions),"unused overlay")
    ledger=r["axis_coverage"]
    require(axis_set(ledger["assessed"])==AXES,"assessed axes")
    declared=axis_set(ledger["represented"])
    if number==18:
        op=correction["0018"]
        require(raw_union-declared=={24,29} and not declared-raw_union
                and set(op["represented_all_records"])==raw_union,"legacy aggregate correction")
    else:
        require(declared==raw_union,"raw axis ledger")
    if number==22:
        require(set(correction["0022"]["represented_all_records"])==effective_union,"effective axis ledger")
    meta={}
    for m in r.get("metadata",[]):
        k=tuple(m["range"]); require(k not in meta,"duplicate metadata"); meta[k]=m
    at=bounds[0]; seen=set(); used_meta=set()
    for c in r["coverage"]:
        lo,hi=c["start"],c["end"]; role=c["role"]; h=c["span_sha256_utf8"]
        require(lo==at,"coverage gap or overlap")
        span(None,lo,hi,role,h,bounds,source)
        ids=c["record_ids"]
        require(isinstance(ids,list) and len(ids)==len(set(ids)),"coverage membership")
        if not ids:
            k=(lo,hi); require(c["disposition"]=="NON_NARRATIVE_METADATA" and k in meta,"unexplained empty coverage")
            m=meta[k]; e=m["evidence"]
            require(m["disposition"]=="NON_NARRATIVE_METADATA" and e["source"]==r["source"]
                    and e["source_sha256_manifest"]==r["source_sha256"]
                    and [e["line_start"],e["line_end"]]==[lo,hi] and e["role"]==role
                    and e["span_sha256_utf8"]==h,"metadata binding")
            span(e,lo,hi,role,h,bounds,source);used_meta.add(k)
        for rid in ids:
            require(rid in rows and rid not in seen,"duplicate or unknown annotation")
            e=rows[rid]["evidence"]
            require(lo<=e["line_start"]<=e["line_end"]<=hi and e["role"]==role,"annotation span")
            seen.add(rid)
        at=hi+1
    require(at==bounds[1]+1 and seen==set(rows) and used_meta==set(meta),"incomplete coverage")
    return rows,counts,len(used_meta)


def sqlite_isolation(rows, overlay):
    """Use native Codex schema in RAM; stage candidates separately, never apply_delta."""
    with sqlite3.connect(":memory:") as db:
        initialize(db)
        db.execute("CREATE TABLE omega_review(id TEXT PRIMARY KEY, authority TEXT NOT NULL, visibility TEXT NOT NULL, promotion INTEGER NOT NULL CHECK(promotion=0))")
        db.executemany("INSERT INTO omega_review VALUES(?,?,?,?)",
                       [(rid,r["authority"],r["visibility"],int(r["promotion"])) for rid,r in rows.items()])
        require(db.execute("SELECT count(*) FROM omega_review").fetchone()[0]==len(overlay),"staging count")
        for table in ("records","codex_events","codex_event_entities","codex_state","codex_episode","codex_pending"):
            require(db.execute("SELECT count(*) FROM "+table).fetchone()[0]==0,"canon isolation")
        try:
            db.execute("INSERT INTO omega_review VALUES('invalid','x','x',1)")
        except sqlite3.IntegrityError:
            pass
        else:
            raise ValueError("promotion constraint")
        require(db.execute("PRAGMA integrity_check").fetchone()[0]=="ok","SQLite integrity")
        return {"staging_rows":len(rows),"typed_events":0,"canonical_records":0,"promotion_constraint":True}


def verify(root, archive=None):
    root=Path(root); d=read(root,ROOT+"book-III-homologation-diagnostic.json",DIAGNOSTIC)
    o=read(root,ROOT+"book-III-consolidated-review-overlay.json",OVERLAY)
    b=read(root,ROOT+"hybrid-approved-baseline.json",BASELINE)
    cp=read(root,"docs/omega008-c-checkpoint.json",blob="4a160e2eedc259e99f0199d00f7b53b4a2476d73")
    q=read(root,cp["bulk"]["macro_queue"],digest=cp["bulk"]["macro_queue_sha256_utf8"])["macros"]
    require(d["archive_pin"]==o["archive_pin"]==b["archive_pin"]==ARCHIVE and o["diagnostic_blob"]==DIAGNOSTIC,"baseline pin")
    require(o["hold"]["production"]=="HOLD" and o["hold"]["macro30"]=="NOT_STARTED" and
            o["hold"]["canon_changed"] is False and o["hold"]["official_checkpoint_changed"] is False,"gate drift")
    require(d["scope"]["source_range"]==[135471,268703] and q[29]["start"]==268704 and q[29]["status"]=="PENDING","book boundary")
    overlays={r["id"]:r for r in o["records"]}; require(len(overlays)==len(o["records"])==886,"overlay IDs")
    corrections={x["macro"]:x for x in b["prior_audit"]["correction_operations"]}
    source=None
    if archive is not None:
        archive=Path(archive)
        require(subprocess.check_output(["git","-C",str(archive),"rev-parse","HEAD"],text=True).strip()==ARCHIVE,"archive checkout")
        require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive dirty")
        manifest=read(archive,"history/sources/MANIFEST.json",blob="2048141263f66151230119af9b0ee51796ac846b")
        source=SourceCache(archive,manifest).get(q[15]["source"])
        head=read(archive,"canon/HEAD.json",blob="9b4e09682fc3148511d59e73ec56fdcda4e396e5")
        require(head["day"]==579,"canonical horizon")
        registry=read(archive,"editorial/registries/universal-codex-design-d580-v1.json",REGISTRY)
        ids={x["id"] for x in registry["records"]+registry["species"]+registry["arcane"]["schools"]+registry["arcane"]["index"]}
        require(all(set(x["candidate_ids"])<=ids for x in o["registry_candidates"]),"registry candidate IDs")
    rows={}; counts=Counter(); coverage=metadata=0
    audits=d["receipt_audits"]; require([x["macro"] for x in audits]==list(range(16,30)),"receipt scope")
    for a in audits:
        n=a["macro"]; r=read(root,a["path"],a["blob"],a["sha256"])
        require([q[n-1]["start"],q[n-1]["end"]]==a["range"] and len(r["records"])==a["records"] and len(r["coverage"])==a["coverage"],"diagnostic counts")
        current,axes,m=validate_macro(r,q[n-1],n,corrections,overlays,source)
        require(not set(rows)&set(current),"duplicate global ID")
        rows.update(current);counts.update(axes);coverage+=len(r["coverage"]);metadata+=m
    require(set(rows)==set(overlays) and coverage==395 and metadata==11,"book totals")
    require({str(k):v for k,v in counts.items()}==d["totals"]["effective_axis_counts_with_existing_overlays"],"effective axis totals")
    require(len({r["evidence"]["span_sha256_utf8"] for r in rows.values()})==886,"anchor uniqueness")
    require(dict(Counter(r["authority"] for r in rows.values()))==d["totals"]["authority"],"authority totals")
    require(dict(Counter(r["visibility"] for r in rows.values()))==d["totals"]["visibility"],"visibility totals")
    require(len(o["controls"])==45 and all(x["promotion"] is False for x in o["controls"]),"control guard")
    require(len(o["registry_candidates"])==211 and all(x["promotion"] is False for x in o["registry_candidates"]),"identity guard")
    isolation=sqlite_isolation(rows,overlays)
    return {"status":"PASS_NATIVE_STAGING_STRUCTURE","records":886,"macros":14,"coverage":coverage,
            "metadata_spans":metadata,"effective_axes":len(counts),"sqlite":isolation,
            "literal_native_reverified":source is not None,"registry_ids_native_checked":source is not None,
            "semantic_certification":False,"independent_review":False,"typed_projection":False,
            "canon_changed":False,"official_checkpoint_changed":False,"next_macro":"NOT_STARTED","gate":"HOLD"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--engine-root",default=".")
    p.add_argument("--archive-root",help="Use only in authorized isolated environment; never public CI.")
    a=p.parse_args()
    print(json.dumps(verify(a.engine_root,a.archive_root),sort_keys=True))


if __name__=="__main__":
    main()
