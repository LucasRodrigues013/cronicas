"""OMEGA TURBO V2: read-only source cache, parallel preparation and receipt integrity.
No semantic inference, API, checkpoint write, or canon promotion.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha1, sha256
from pathlib import Path
import argparse
import json
import re
import time

AXES = set(range(1, 31))
ROLES = {"## Prompt:": "Prompt", "## Response:": "Response"}


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def digest(value):
    return sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def git_blob(raw):
    return sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class SourceCache:
    def __init__(self, archive, manifest):
        self.archive = Path(archive).resolve()
        self.sources = {x["source_name"]: x for x in manifest["sources"]}
        self.cached = {}
        self.loads = 0

    def get(self, name):
        if name in self.cached:
            return self.cached[name]
        meta = self.sources[name]
        parts = []
        for p in meta["parts"]:
            path = (self.archive / p["path"]).resolve()
            require(path.is_relative_to(self.archive), "source escapes archive")
            raw = path.read_bytes()
            require(len(raw) == p["bytes"] and git_blob(raw) == p["git_blob_sha1"], "part mismatch")
            parts.append(raw)
        raw = b"".join(parts)
        require(len(raw) == meta["utf8_bytes"] and digest(raw) == meta["sha256"], "source mismatch")
        lines = raw.decode("utf-8").split("\n")
        roles = []
        role = "Metadata"
        for line in lines:
            role = ROLES.get(line.strip(), role)
            roles.append(role)
        # Physical parts may divide a logical line or UTF-8 character.
        extents, offset = [], 1
        for p, data in zip(meta["parts"], parts):
            end = offset + data.count(b"\n")
            extents.append((offset, end-int(data.endswith(b"\n")), p["git_blob_sha1"]))
            offset = end
        result = (tuple(lines), tuple(roles), tuple(extents), meta["sha256"])
        self.cached[name] = result
        self.loads += 1
        return result


def anchor(source, lo, hi):
    lines = source[0]
    require(type(lo) is int and type(hi) is int and 1 <= lo <= hi <= len(lines), "bad span")
    return digest("\n".join(lines[lo-1:hi]))


def plan_macro(macro, source, max_lines=300, context=12):
    require(1 <= max_lines <= 600 and 0 <= context <= 50, "bad geometry")
    lo, hi = macro["start"], macro["end"]
    require(hi-lo+1 == macro["lines"], "macro geometry")
    lines, roles = source[:2]
    units = []
    at = lo
    while at <= hi:
        end = min(at+max_lines-1, hi)
        role = roles[at-1]
        for n in range(at+1, end+1):
            if roles[n-1] != role:
                end = n-1
                break
        left, right = at, end
        while left > max(1, at-context) and roles[left-2] == role:
            left -= 1
        while right < min(len(lines), end+context) and roles[right] == role:
            right += 1
        units.append(dict(start=at, end=end, role=role, sha256=anchor(source,at,end),
                          context_start=left, context_end=right, context_sha256=anchor(source,left,right)))
        at = end+1
    require(sum(u["end"]-u["start"]+1 for u in units)==macro["lines"], "unit coverage")
    return dict(macro_id=macro["id"], range=[lo,hi], lines=macro["lines"], units=units,
                status="PREPARED_NOT_SEMANTICALLY_RECOVERED", official_unit_seal=macro.get("unit_seal"),
                window_geometry="WORK_WINDOWS_NOT_OFFICIAL_QUEUE_UNITS")


def prepare_pair(cache, macros, cursor):
    require(len(macros)==2 and macros[0]["start"]==cursor, "cursor mismatch")
    a,b=macros
    require(b["previous_macro"]==a["id"] and a["source"]==b["source"] and a["end"]+1==b["start"], "chain mismatch")
    sources=[cache.get(m["source"]) for m in macros]
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(plan_macro,m,s) for m,s in zip(macros,sources)]
        return [f.result() for f in jobs]


def validate_receipt(receipt, macro, source, project, archive_pin, previous_ids=(), expected_range=None):
    r=receipt
    bounds=expected_range or [macro["start"],macro["end"]]
    require(r["project"]==project and r["archive_pin"]==archive_pin, "project/pin mismatch")
    require(r["macro_id"]==macro["id"] and r["range"]==bounds and r["next_line"]==bounds[1]+1, "macro mismatch")
    require(r["source"]==macro["source"] and r["source_sha256"]==source[3], "source mismatch")
    require(r["canon_changed"] is False and r["semantic_certification"] is False and r.get("promotion",False) is False and r.get("independent_review",False) is False, "false authority")
    ids=set(previous_ids); current={}; represented=set()
    def check_span(lo,hi,role,h):
        require(bounds[0]<=lo<=hi<=bounds[1], "out of macro")
        require(role in ("Prompt","Response") and all(x==role for x in source[1][lo-1:hi]), "role mismatch")
        require(anchor(source,lo,hi)==h,"hash mismatch")
    for rec in r["records"]:
        e=rec["evidence"];lo,hi=e["line_start"],e["line_end"]
        require(rec["id"] not in ids and rec["promotion"] is False, "duplicate/promotion")
        require(e["source"]==macro["source"] and e["source_sha256_manifest"]==source[3], "evidence source")
        check_span(lo,hi,e["role"],e["span_sha256_utf8"])
        blobs={p[2] for p in source[2] if p[0]<=hi and p[1]>=lo}
        require(e["blob_sha1"] in blobs and set(e.get("blob_sha1_parts",[e["blob_sha1"]]))==blobs,"physical provenance")
        require(rec["axes"] and all(type(i) is int and i in AXES for i in rec["axes"]),"axis mismatch")
        require("NO_CHARACTER_INJECTION" in rec["visibility"], "visibility")
        require(e["role"]!="Prompt" or rec["authority"] in ("AUTHOR_REQUEST_OR_CHOICE","AUTHOR_DIRECTION_NOT_EVENT"),"prompt promoted")
        require(rec["type"] not in ("reader-only","reader-perspectives","dream","variant") or rec["visibility"].startswith("READER_ONLY"),"perspective leakage")
        ids.add(rec["id"]);current[rec["id"]]=e;represented.update(rec["axes"])
    seen=set();at=bounds[0]
    for row in r["coverage"]:
        lo,hi=row["start"],row["end"]
        require(lo==at,"coverage gap/overlap")
        check_span(lo,hi,row["role"],row["span_sha256_utf8"])
        require(not any(x.strip() in ROLES for x in source[0][lo:hi]),"hidden role boundary")
        require(row["record_ids"],"empty annotations")
        for rid in row["record_ids"]:
            require(rid in current and rid not in seen,"missing/duplicate annotation")
            e=current[rid];require(lo<=e["line_start"]<=e["line_end"]<=hi,"annotation outside section")
            seen.add(rid)
        at=hi+1
    require(at==bounds[1]+1 and seen==set(current),"incomplete coverage")
    require(set(r["axis_coverage"]["assessed"])==AXES and set(r["axis_coverage"]["represented"])==represented,"axis ledger mismatch")
    return dict(records=len(current),coverage=len(r["coverage"]),lines=bounds[1]-bounds[0]+1,
                axes_assessed=30,axes_represented=sorted(represented),status="STRUCTURAL_PASS_NOT_SEMANTIC_CERTIFICATION")


def main():
    p=argparse.ArgumentParser();p.add_argument("--archive-root",required=True);p.add_argument("--manifest",required=True);p.add_argument("--engine-root",required=True)
    args=p.parse_args();t=time.perf_counter();root=Path(args.engine_root)
    cp=json.loads((root/"docs/omega008-c-checkpoint.json").read_bytes());raw=(root/cp["bulk"]["macro_queue"]).read_bytes()
    require(digest(raw)==cp["bulk"]["macro_queue_sha256_utf8"],"queue hash mismatch")
    require(cp["archive_head"]["day"]==579 and cp["archive_head"]["pending"]=="LVI-C09-PII-D580-AUTHOR-SOURCE" and not cp["canon_changed"],"archive horizon")
    macros=json.loads(raw)["macros"];i=len(cp["bulk"]["recovered_macro_ids"])
    require(len(macros)==cp["bulk"]["macro_count"] and macros[i]==cp["bulk"]["next_macro"],"queue mismatch")
    cache=SourceCache(args.archive_root,json.loads(Path(args.manifest).read_bytes()))
    plans=prepare_pair(cache,macros[i:i+2],cp["bulk"]["recovery_cursor"])
    print(json.dumps(dict(status="PREPARATION_ONLY",macros=[dict(range=x["range"],lines=x["lines"],units=len(x["units"])) for x in plans],source_loads=cache.loads,elapsed_seconds=round(time.perf_counter()-t,6),semantic_certification=False,canon_changed=False)))


if __name__=="__main__":
    main()
